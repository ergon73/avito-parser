# genai-step4-readme.md: Обработка данных, SQLite и контейнеризация Docker

## ТРЕБОВАНИЯ

✅ Step 3 завершен, парсер работает стабильно и обходит базовые блокировки.
✅ Структура проекта сохранена.
✅ Установлен DBeaver (или другой SQLite-клиент) и Docker Desktop.

## ЦЕЛЬ ЭТАПА 4

Превратить парсер из сборщика HTML в полноценный инструмент для работы с данными:

1.  **Создать процессор данных** на BeautifulSoup для извлечения информации из HTML.
2.  **Определить модель данных** для объявлений.
3.  **Реализовать сохранение** структурированных данных в базу данных SQLite.
4.  **Внедрить проверку на дубликаты**, чтобы не сохранять одни и те же объявления.
5.  [cite\_start]**Упаковать финальное приложение в Docker-контейнер** для легкого запуска и переноса. [cite: 71, 147]

-----

## ШАГ 1: СОЗДАНИЕ МОДЕЛИ ДАННЫХ И МЕНЕДЖЕРА БД

Сначала определим, *что* мы сохраняем и *как*.

### 1.1 Создайте файл `database/models.py`

Это будет определять структуру каждого объявления.

```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Listing:
    """Модель данных для одного объявления Avito."""
    url: str
    title: str
    price: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = field(default_factory=list)
    
    # Дополнительные поля из урока
    bail: Optional[str] = None      # Залог
    tax: Optional[str] = None       # Комиссия
    services: Optional[str] = None  # ЖКУ
```

### 1.2 Создайте файл `database/database_manager.py`

Этот модуль будет управлять подключением и записью в SQLite.

```python
import sqlite3
from typing import Optional
from config.settings import logger
from database.models import Listing
import json
import os

class DatabaseManager:
    """Управляет операциями с базой данных SQLite."""
    
    def __init__(self, db_path: str = "database/avito_listings.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_table()

    def _connect(self):
        """Устанавливает соединение с БД."""
        try:
            self._connection = sqlite3.connect(self.db_path)
            logger.debug(f"Успешное подключение к БД: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            self._connection = None

    def _create_table(self):
        """Создает таблицу для объявлений, если она не существует."""
        if not self._connection:
            return
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            price TEXT,
            address TEXT,
            description TEXT,
            images TEXT, -- Сохраняем как JSON-строку
            bail TEXT,
            tax TEXT,
            services TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(create_table_query)
            self._connection.commit()
            logger.debug("Таблица 'listings' готова к работе.")
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания таблицы: {e}")

    def add_listing(self, listing: Listing) -> bool:
        """Добавляет объявление в БД, избегая дубликатов по URL."""
        if not self._connection:
            logger.error("Нет подключения к БД.")
            return False
            
        # [cite_start]Проверка на дубликат [cite: 127]
        if self._listing_exists(listing.url):
            logger.debug(f"Объявление уже существует: {listing.url}")
            return False

        insert_query = """
        INSERT INTO listings (url, title, price, address, description, images, bail, tax, services)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        images_json = json.dumps(listing.images)
        data = (
            listing.url, listing.title, listing.price, listing.address,
            listing.description, images_json, listing.bail, listing.tax, listing.services
        )

        try:
            cursor = self._connection.cursor()
            cursor.execute(insert_query, data)
            self._connection.commit()
            logger.trace(f"Добавлено новое объявление: {listing.title}")
            return True
        except sqlite3.IntegrityError:
            # На случай, если проверка _listing_exists не сработала
            logger.warning(f"Объявление уже существует (UNIQUE constraint): {listing.url}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления объявления: {e}")
            return False

    def _listing_exists(self, url: str) -> bool:
        """Проверяет наличие объявления по URL."""
        if not self._connection:
            return False
        
        query = "SELECT 1 FROM listings WHERE url = ? LIMIT 1;"
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, (url,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Ошибка проверки существования объявления: {e}")
            return False
            
    def close(self):
        """Закрывает соединение с БД."""
        if self._connection:
            self._connection.close()
            logger.debug("Соединение с БД закрыто.")

# Создаем единый экземпляр для всего приложения
db_manager = DatabaseManager()
```

-----

## ШАГ 2: СОЗДАНИЕ HTML-ПРОЦЕССОРА

Этот модуль будет "разбирать" HTML и превращать его в структурированные данные.

### 2.1 Создайте `services/avito_processor.py`

```python
from bs4 import BeautifulSoup
from typing import List
from database.models import Listing
from config.settings import logger
from urllib.parse import urljoin

class AvitoProcessor:
    """Извлекает структурированные данные из HTML-кода страницы Avito."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def process_html(self, html: str) -> List[Listing]:
        """
        Основной метод для парсинга HTML.
        [cite_start]Находит все объявления на странице и извлекает из них данные. [cite: 98]
        """
        soup = BeautifulSoup(html, 'lxml')
        listings = []
        
        # [cite_start]Находим корневой блок со всеми объявлениями [cite: 99, 211]
        items_container = soup.find("div", {"data-marker": "catalog-serp"})
        if not items_container:
            logger.warning("Контейнер с объявлениями не найден. Возможно, структура страницы изменилась.")
            return []

        # Ищем все карточки объявлений внутри контейнера
        items = items_container.find_all("div", {"data-marker": "item"})
        logger.info(f"Найдено {len(items)} карточек объявлений на странице.")

        for item in items:
            try:
                listing = self._parse_item(item)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.error(f"Ошибка при обработке карточки: {e}")
        
        return listings

    def _parse_item(self, item_soup: BeautifulSoup) -> Listing:
        """Извлекает данные из одной карточки объявления."""
        
        title_tag = item_soup.find("h3", {"data-marker": "item-title"})
        link_tag = item_soup.find("a", {"data-marker": "item-title"})
        
        if not title_tag or not link_tag:
            return None

        title = title_tag.text.strip()
        relative_url = link_tag['href']
        absolute_url = urljoin(self.base_url, relative_url)
        
        price = self._get_text(item_soup, "meta", {"itemprop": "price"})
        address = self._get_text(item_soup, "div", {"data-marker": "item-address"})
        description = self._get_text(item_soup, "div", {"class": "iva-item-description"})

        # [cite_start]Парсинг изображений из карусели [cite: 117]
        images = self._parse_images(item_soup)

        return Listing(
            url=absolute_url,
            title=title,
            price=price,
            address=address.split(',')[0] if address else None, # Убираем лишнее
            description=description,
            images=images
        )
    
    def _get_text(self, soup: BeautifulSoup, tag: str, attrs: dict) -> str:
        """Безопасно извлекает текст из тега."""
        element = soup.find(tag, attrs)
        if tag == "meta" and element:
            return element.get('content', '').strip()
        return element.text.strip() if element else None

    def _parse_images(self, item_soup: BeautifulSoup) -> List[str]:
        """
        [cite_start]Извлекает ссылки на изображения из карусели, выбирая самые большие. [cite: 125]
        """
        images = []
        gallery = item_soup.find("ul", class_=lambda x: x and 'images-list' in x)
        if not gallery:
            return []
            
        img_tags = gallery.find_all("img")
        [cite_start]for img in img_tags[:3]:  # Берем только первые 3 фото, как в уроке [cite: 49]
            if 'srcset' in img.attrs:
                # В srcset ссылки на разные размеры, берем самую последнюю (самую большую)
                largest_image_url = img['srcset'].split(',')[-1].strip().split(' ')[0]
                images.append(largest_image_url)
        return images
```

-----

## ШАГ 3: ИНТЕГРАЦИЯ В MAIN.PY

Теперь объединим все части: парсер получает HTML, процессор его разбирает, а менеджер БД сохраняет.

### 3.1 Обновите `main.py`

Полностью замените содержимое файла.

```python
import sys
from config.settings import settings, logger
from core.playwright_parser import PlaywrightParser
from core.curl_parser import CurlParser
from core.hybrid_parser import HybridParser
from core.local_parser import LocalParser
from services.avito_processor import AvitoProcessor
from database.database_manager import db_manager

def get_parser(mode: str):
    """Фабрика парсеров (полная версия)"""
    if settings.use_local_html:
        logger.info("Режим: работа с локальным HTML")
        return LocalParser()
    
    if mode == "playwright":
        return PlaywrightParser()
    elif mode == "curl":
        return CurlParser()
    elif mode == "hybrid":
        return HybridParser()
    else:
        logger.warning(f"Неизвестный режим {mode}, используем playwright")
        return PlaywrightParser()

def main():
    logger.info("=== Avito Parser v3.0 (Data & Docker) ===")
    
    if settings.use_antibot_tricks:
        logger.warning("⚠️ РЕЖИМ ОБХОДА ЗАЩИТ ВКЛЮЧЕН")
    else:
        logger.info("✅ Стандартный режим")
    
    if not settings.use_local_html and not settings.target_url:
        logger.error("Не задан TARGET_URL в .env")
        sys.exit(1)
    
    # 1. ПОЛУЧЕНИЕ HTML
    parser = get_parser(settings.parser_mode)
    try:
        url = None if settings.use_local_html else settings.target_url
        html = parser.parse(url)
        
        if not html:
            logger.error("Не удалось получить HTML. Завершение работы.")
            sys.exit(1)
            
        # 2. ОБРАБОТКА HTML И ИЗВЛЕЧЕНИЕ ДАННЫХ
        logger.info("Начало обработки HTML...")
        processor = AvitoProcessor(base_url=settings.target_url)
        listings = processor.process_html(html)
        
        if not listings:
            logger.warning("Не удалось извлечь ни одного объявления. Проверьте селекторы в avito_processor.py")
            sys.exit(0)
            
        # 3. СОХРАНЕНИЕ В БАЗУ ДАННЫХ
        added_count = 0
        for listing in listings:
            if db_manager.add_listing(listing):
                added_count += 1
        
        logger.success("="*50)
        logger.success(f"         ОБРАБОТКА ЗАВЕРШЕНА")
        logger.success(f"  Всего найдено на странице: {len(listings)}")
        logger.success(f"  Новых добавлено в БД: {added_count}")
        logger.success("="*50)
        
    except Exception as e:
        logger.exception(f"Критическая ошибка в главном цикле: {e}")
        sys.exit(1)
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
```

-----

## ШАГ 4: КОНТЕЙНЕРИЗАЦИЯ ПРИЛОЖЕНИЯ С ПОМОЩЬЮ DOCKER

[cite\_start]Последний шаг — упаковка нашего приложения в Docker-контейнер для изоляции и простоты развертывания. [cite: 152, 170]

### 4.1 Создайте `Dockerfile` в корне проекта

```dockerfile
# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем системные зависимости для Playwright
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем браузер для Playwright
RUN python -m playwright install chromium --with-deps

# Копируем весь код приложения в контейнер
COPY . .

# Указываем команду для запуска приложения
CMD ["python", "main.py"]
```

### 4.2 Создайте `docker-compose.yml` в корне проекта

Этот файл упрощает управление контейнером.

```yaml
services:
  avito-parser:
    build: .
    container_name: avito-parser-app
    # Монтируем базу данных и логи, чтобы они не терялись при перезапуске контейнера
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
      - ./trash:/app/trash
    # [cite_start]Подключаем .env файл для конфигурации [cite: 193]
    env_file:
      - .env

```

-----

## ПРОВЕРКА И ЗАПУСК

### Локальный запуск (без Docker):

1.  Удалите старый файл `database/avito_listings.db`, чтобы начать с чистого листа.
2.  Запустите парсер: `python main.py`.
3.  Проверьте консоль. [cite\_start]Вы должны увидеть статистику о найденных и добавленных объявлениях. [cite: 102]
4.  [cite\_start]Откройте файл `database/avito_listings.db` в DBeaver и убедитесь, что таблица `listings` заполнилась данными, включая ссылки на изображения. [cite: 91, 141]

### Запуск через Docker:

1.  Убедитесь, что Docker Desktop запущен.
2.  [cite\_start]Откройте терминал в корне проекта и выполните команду для сборки и запуска контейнера: [cite: 160]
    ```bash
    docker-compose up --build
    ```
3.  Наблюдайте за логами в терминале. Вы должны увидеть тот же вывод, что и при локальном запуске.
4.  После завершения работы контейнера, проверьте файл `database/avito_listings.db` на вашем компьютере. Данные должны быть на месте, так как мы "пробросили" папку `database` внутрь контейнера.
5.  Чтобы остановить контейнер, нажмите `Ctrl+C` в терминале.
