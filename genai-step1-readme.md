# GENAI-STEP1-README: Базовый Avito Parser

## ЦЕЛЬ ЭТАПА 1
Создать работающий парсер на Playwright, который:
- Загружает страницу Avito из .env
- Сохраняет полный HTML в trash/
- Выводит весь HTML в консоль для анализа
- Готов к расширению до гибридной версии

## ⚠️ ЮРИДИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ
Использование для образовательных целей. Пользователь берет на себя ответственность.

---

## ЭТАП 0: ПОДГОТОВКА

### Команды настройки окружения:

**Windows PowerShell:**
```powershell
python -m venv .venv
# При ошибке политики:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

---

## ЭТАП 1: СТРУКТУРА ПРОЕКТА

Создай структуру:
```
project_root/
├── config/
│   └── settings.py
├── core/
│   ├── __init__.py
│   ├── base_parser.py      # ABC интерфейс (ВАЖНО!)
│   └── playwright_parser.py
├── services/
│   ├── __init__.py
│   ├── headers.py          # (перенести сюда)
│   ├── user_agent_pc.txt   # (перенести сюда)
│   └── data_manager.py
├── utils/
│   ├── __init__.py
│   └── file_manager.py
├── trash/                   # Для HTML файлов
├── logs/                    # Для логов
├── cookies/                 # Для будущих cookies
├── .env.example
├── .gitignore
├── requirements.txt
└── main.py
```

### .gitignore:
```
.venv/
venv/
.env
__pycache__/
*.pyc
trash/*.html
cookies/*.json
logs/*.log
.DS_Store
.idea/
.vscode/
.cursor/
```

### .env.example:
```env
# URL для парсинга
TARGET_URL=https://www.avito.ru/city/kvartiry/sdam/na_dlitelnyy_srok

# Режим работы (пока только playwright, позже добавим другие)
PARSER_MODE=playwright

# Заготовки для будущего расширения
USE_ANTIBOT_TRICKS=false
USE_LOCAL_HTML=false
LOCAL_HTML_PATH=trash/avito_page.html
LOG_LEVEL=INFO
```

---

## ЭТАП 2: ЗАВИСИМОСТИ

### requirements.txt (БЕЗ версий!):
```
playwright
python-dotenv
loguru
beautifulsoup4
curl-cffi
asyncio
aiofiles
```

⚠️ Даже если не все используются сейчас - ставим сразу для будущего

---

## ЭТАП 3: РЕАЛИЗАЦИЯ МОДУЛЕЙ

### 3.1 config/settings.py
```python
import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv
from loguru import logger

# Загрузка .env
load_dotenv()

@dataclass
class Settings:
    # Основные настройки
    target_url: str = os.getenv("TARGET_URL", "")
    parser_mode: str = os.getenv("PARSER_MODE", "playwright")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Заготовки для расширения
    use_antibot_tricks: bool = os.getenv("USE_ANTIBOT_TRICKS", "false").lower() == "true"
    use_local_html: bool = os.getenv("USE_LOCAL_HTML", "false").lower() == "true"
    local_html_path: str = os.getenv("LOCAL_HTML_PATH", "")

settings = Settings()

# Настройка логирования
logger.remove()
logger.add(sys.stdout, level=settings.log_level, 
           format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
logger.add("logs/app.log", level="DEBUG", rotation="10 MB")
```

### 3.2 core/base_parser.py (КРИТИЧНО для будущего расширения!)
```python
from abc import ABC, abstractmethod
from typing import Optional

class BaseParser(ABC):
    """Базовый интерфейс для всех парсеров"""
    
    @abstractmethod
    def parse(self, url: str) -> Optional[str]:
        """Получает HTML со страницы"""
        pass
    
    def check_blocking(self, content: str) -> bool:
        """Проверка на блокировку"""
        if not content:
            return True
        
        block_keywords = [
            "Проблема с IP",
            "Доступ с Вашего IP временно ограничен",
            "captcha",
            "cloudflare"
        ]
        
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in block_keywords)
```

### 3.3 services/data_manager.py
```python
import random
from typing import List, Dict
from loguru import logger

class DataManager:
    """Управление headers и user agents"""
    
    def __init__(self):
        self.headers = self._load_headers()
        self.user_agents = self._load_user_agents()
    
    def _load_headers(self) -> Dict[str, str]:
        """Загрузка headers из файла"""
        try:
            from services.headers import CUSTOM_HEADERS
            return CUSTOM_HEADERS
        except ImportError:
            logger.warning("headers.py не найден, используем базовые")
            return {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept-language': 'ru-RU,ru;q=0.9',
            }
    
    def _load_user_agents(self) -> List[str]:
        """Загрузка user agents из файла"""
        try:
            with open('services/user_agent_pc.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.warning("user_agent_pc.txt не найден, используем базовый")
            return ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
    
    def get_random_user_agent(self) -> str:
        """Случайный user agent"""
        return random.choice(self.user_agents) if self.user_agents else self.user_agents[0]

data_manager = DataManager()
```

### 3.4 core/playwright_parser.py
```python
from core.base_parser import BaseParser
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from services.data_manager import data_manager
from typing import Optional
from loguru import logger
import time

class PlaywrightParser(BaseParser):
    """Парсер на Playwright"""
    
    def parse(self, url: str) -> Optional[str]:
        """Загружает страницу и возвращает HTML"""
        
        user_agent = data_manager.get_random_user_agent()
        logger.info(f"[Playwright] Запуск браузера...")
        logger.debug(f"[Playwright] UA: {user_agent}")
        
        try:
            with sync_playwright() as p:
                # Запуск браузера
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                # Создание контекста
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1920, 'height': 1080},
                    locale='ru-RU',
                )
                
                # Новая страница
                page = context.new_page()
                
                logger.info(f"[Playwright] Переход на {url}")
                
                # Загрузка страницы
                response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                if response and not response.ok:
                    logger.error(f"[Playwright] HTTP {response.status}")
                
                # ВАЖНО для Avito: ждем загрузки каталога
                try:
                    page.wait_for_selector("div[data-marker='catalog-serp']", timeout=20000)
                    logger.success("[Playwright] Каталог загружен")
                except PlaywrightTimeoutError:
                    logger.warning("[Playwright] Каталог не найден (возможна блокировка)")
                
                # Дополнительное ожидание полной загрузки
                page.wait_for_load_state('networkidle', timeout=30000)
                
                # Получаем HTML
                content = page.content()
                
                # Закрываем
                browser.close()
                
                logger.success(f"[Playwright] Получено {len(content):,} байт")
                
                # Проверка на блокировку
                if self.check_blocking(content):
                    logger.warning("[Playwright] Обнаружена блокировка!")
                
                return content
                
        except PlaywrightTimeoutError:
            logger.error("[Playwright] Timeout")
            return None
        except Exception as e:
            logger.error(f"[Playwright] Ошибка: {e}")
            if "Executable not found" in str(e):
                logger.error("Выполните: playwright install chromium")
            return None
```

### 3.5 utils/file_manager.py
```python
import os
from datetime import datetime
from loguru import logger
from urllib.parse import urlparse

def save_html(content: str, url: str, folder: str = "trash") -> str:
    """Сохраняет HTML в файл"""
    
    if not content:
        logger.warning("Нет контента для сохранения")
        return None
    
    # Создаем папку
    os.makedirs(folder, exist_ok=True)
    
    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = urlparse(url).netloc.replace('.', '_')
    filename = f"{timestamp}_{domain}.html"
    filepath = os.path.join(folder, filename)
    
    # Сохраняем
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.success(f"Сохранено: {filepath} ({len(content):,} байт)")
        return filepath
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return None
```

### 3.6 main.py
```python
import sys
from config.settings import settings, logger
from core.playwright_parser import PlaywrightParser
from utils.file_manager import save_html

def get_parser(mode: str):
    """Фабрика парсеров (готова к расширению)"""
    if mode == "playwright":
        return PlaywrightParser()
    elif mode == "curl":
        logger.info("curl парсер будет добавлен в Step 2")
        return PlaywrightParser()  # Временно
    elif mode == "hybrid":
        logger.info("hybrid режим будет добавлен в Step 2")
        return PlaywrightParser()  # Временно
    else:
        logger.error(f"Неизвестный режим: {mode}")
        return PlaywrightParser()

def main():
    logger.info("=== Avito Parser v1.0 (Step 1: Base) ===")
    
    # Проверка настроек
    if not settings.target_url:
        logger.error("Не задан TARGET_URL в .env")
        sys.exit(1)
    
    logger.info(f"URL: {settings.target_url}")
    logger.info(f"Режим: {settings.parser_mode}")
    
    # Получаем парсер
    parser = get_parser(settings.parser_mode)
    
    # Парсим
    try:
        html = parser.parse(settings.target_url)
        
        if html:
            # Сохраняем
            filepath = save_html(html, settings.target_url)
            
            # Анализ
            if "catalog-serp" in html:
                logger.success("✓ Каталог найден в HTML")
            else:
                logger.warning("⚠ Каталог не найден")
            
            # ПОЛНЫЙ вывод в консоль (как в уроке!)
            print("\n" + "="*50)
            print("ПОЛНЫЙ HTML (для анализа структуры):")
            print("="*50)
            print(html)  # БЕЗ ОГРАНИЧЕНИЙ!
            print("="*50)
            print(f"Размер: {len(html):,} байт")
            print(f"Файл: {filepath}")
            
        else:
            logger.error("Не удалось получить HTML")
            logger.info("Попробуйте:")
            logger.info("1. Проверить URL")
            logger.info("2. Использовать VPN/прокси")
            logger.info("3. Попробовать позже")
            
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Проверка Playwright
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception:
        logger.error("Playwright не готов!")
        logger.info("Выполните: playwright install chromium")
        sys.exit(1)
    
    main()
```

---

## ПРОВЕРКА РЕЗУЛЬТАТА

1. Создать .env из .env.example (ВРУЧНУЮ!)
2. Запустить: `python main.py`
3. Должно появиться:
   - HTML файл в trash/
   - Полный HTML в консоли
   - Логи работы

## ГОТОВНОСТЬ К STEP 2

✅ Архитектура с BaseParser готова к расширению
✅ Фабрика парсеров готова к новым типам
✅ Все зависимости уже установлены
✅ Настройки подготовлены для новых режимов

---

## ЕСЛИ БЛОКИРОВКА

Это нормально! В Step 2 добавим:
- curl-cffi для обхода TLS fingerprinting
- Антидетект техники
- Гибридный режим
- Работу с локальными HTML

Пока используйте VPN или сохраненные HTML из урока.