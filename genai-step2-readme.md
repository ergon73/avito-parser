# GENAI-STEP2-README: Апгрейд до полной версии

## ТРЕБОВАНИЯ
✅ Step 1 должен работать (Playwright парсит и сохраняет HTML)
✅ Структура проекта из Step 1 сохранена
✅ Все зависимости уже установлены

## ЦЕЛЬ ЭТАПА 2
Добавить в существующий проект:
1. **curl-cffi парсер** для быстрой работы и обхода TLS
2. **Гибридный режим** с умным переключением
3. **Антибот техники** (опционально включаемые)
4. **Локальный парсер** для работы с сохраненными HTML

---

## НОВЫЕ МОДУЛИ ДЛЯ СОЗДАНИЯ

### 1. services/antibot_toolkit.py
```python
import random
import time
from config.settings import settings, logger
from services.data_manager import data_manager

class AntibotToolkit:
    """Набор техник для обхода защит (используется опционально)"""
    
    def __init__(self):
        self.enabled = settings.use_antibot_tricks
        
    def get_random_headers(self):
        """Возвращает headers с учетом настроек"""
        if not self.enabled:
            # Стандартные headers
            return {
                'accept': 'text/html,application/xhtml+xml,application/xml',
                'accept-language': 'ru-RU,ru;q=0.9',
                'user-agent': data_manager.get_random_user_agent()
            }
        
        # Режим обхода - полный набор + рандомизация
        headers = data_manager.headers.copy()
        headers['user-agent'] = data_manager.get_random_user_agent()
        
        # Добавляем случайные заголовки
        if random.random() > 0.5:
            headers['referer'] = 'https://www.google.com/'
        
        return headers
    
    def get_browser_context(self):
        """Настройки контекста для Playwright"""
        base_context = {
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'ru-RU',
            'timezone_id': 'Europe/Moscow',
        }
        
        if not self.enabled:
            return base_context
            
        # Дополнительная рандомизация
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
        ]
        base_context['viewport'] = random.choice(viewports)
        
        return base_context
    
    def get_stealth_script(self):
        """JavaScript для скрытия автоматизации"""
        if not self.enabled:
            return None
            
        return """
        // Скрываем webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Добавляем плагины
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Правильные языки
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ru-RU', 'ru', 'en-US', 'en']
        });
        
        // Chrome объект
        window.chrome = {
            runtime: {},
        };
        """
    
    def get_random_delay(self):
        """Случайная задержка для имитации человека"""
        if not self.enabled:
            return 0
        return random.uniform(0.5, 3.0)
    
    def get_impersonate_target(self):
        """Случайная цель для curl-cffi"""
        targets = ["chrome110", "chrome120", "edge99", "safari15_5"]
        return random.choice(targets) if self.enabled else "chrome110"

antibot_toolkit = AntibotToolkit()
```

### 2. core/curl_parser.py
```python
from core.base_parser import BaseParser
from curl_cffi import requests
from typing import Optional
from services.antibot_toolkit import antibot_toolkit
from loguru import logger
import json
import os

class CurlParser(BaseParser):
    """Парсер на curl-cffi для обхода TLS fingerprinting"""
    
    def __init__(self):
        self.session = requests.Session()
        self.cookies_file = "cookies/curl_cookies.json"
        self._load_cookies()
    
    def _load_cookies(self):
        """Загрузка сохраненных cookies"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        self.session.cookies.set(**cookie)
                logger.debug("[curl] Cookies загружены")
            except Exception as e:
                logger.warning(f"[curl] Ошибка загрузки cookies: {e}")
    
    def _save_cookies(self):
        """Сохранение cookies"""
        os.makedirs("cookies", exist_ok=True)
        cookies = []
        for cookie in self.session.cookies:
            cookies.append({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path
            })
        with open(self.cookies_file, 'w') as f:
            json.dump(cookies, f)
    
    def parse(self, url: str) -> Optional[str]:
        """Быстрая загрузка через curl-cffi"""
        
        headers = antibot_toolkit.get_random_headers()
        impersonate = antibot_toolkit.get_impersonate_target()
        
        logger.info(f"[curl] Запрос к {url}")
        logger.debug(f"[curl] Impersonate: {impersonate}")
        
        # Retry логика
        for attempt in range(3):
            try:
                if settings.use_antibot_tricks:
                    # С обходом защит
                    response = self.session.get(
                        url,
                        headers=headers,
                        impersonate=impersonate,
                        timeout=30
                    )
                else:
                    # Простой запрос
                    response = self.session.get(
                        url,
                        headers=headers,
                        timeout=30
                    )
                
                # Сохраняем cookies
                self._save_cookies()
                
                content = response.text
                
                # Проверка на блокировку
                if self.check_blocking(content):
                    logger.warning(f"[curl] Блокировка (попытка {attempt + 1}/3)")
                    if attempt < 2:
                        time.sleep(antibot_toolkit.get_random_delay())
                        continue
                    return content  # Возвращаем что есть
                
                if len(content) < 10000:
                    logger.warning(f"[curl] Короткий ответ: {len(content)} байт")
                
                logger.success(f"[curl] Успешно: {len(content):,} байт")
                return content
                
            except Exception as e:
                logger.error(f"[curl] Ошибка (попытка {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                return None
        
        return None
```

### 3. core/hybrid_parser.py
```python
from core.base_parser import BaseParser
from core.curl_parser import CurlParser
from core.playwright_parser import PlaywrightParser
from typing import Optional
from config.settings import settings, logger
import time

class HybridParser(BaseParser):
    """Гибридный парсер с умным переключением"""
    
    def __init__(self):
        self.curl_parser = CurlParser()
        self._playwright_parser = None  # Ленивая инициализация
        self.stats = {
            'curl_success': 0,
            'curl_fail': 0,
            'playwright_success': 0,
            'playwright_fail': 0
        }
    
    @property
    def playwright_parser(self):
        """Ленивая загрузка Playwright"""
        if self._playwright_parser is None:
            self._playwright_parser = PlaywrightParser()
        return self._playwright_parser
    
    def parse(self, url: str) -> Optional[str]:
        """Умное переключение между парсерами"""
        
        logger.info("[Hybrid] Начинаем гибридный парсинг")
        
        if not settings.use_antibot_tricks:
            # Стандартный режим - Playwright первый (для Avito)
            return self._standard_mode(url)
        else:
            # Режим обхода - анализ через curl, работа через Playwright
            return self._antibot_mode(url)
    
    def _standard_mode(self, url: str) -> Optional[str]:
        """Стандартный режим: Playwright → curl"""
        
        logger.info("[Hybrid] Стандартный режим: начинаем с Playwright")
        
        # Playwright для JS-контента
        start = time.time()
        content = self.playwright_parser.parse(url)
        elapsed = time.time() - start
        
        if content and self._is_valid_content(content):
            logger.success(f"[Hybrid] Playwright успешно ({elapsed:.1f}с)")
            self.stats['playwright_success'] += 1
            self._show_stats()
            return content
        
        self.stats['playwright_fail'] += 1
        
        # Fallback на curl
        logger.info("[Hybrid] Пробуем curl как альтернативу")
        start = time.time()
        content = self.curl_parser.parse(url)
        elapsed = time.time() - start
        
        if content:
            logger.info(f"[Hybrid] curl вернул контент ({elapsed:.1f}с)")
            self.stats['curl_success'] += 1
        else:
            self.stats['curl_fail'] += 1
        
        self._show_stats()
        return content
    
    def _antibot_mode(self, url: str) -> Optional[str]:
        """Режим обхода: быстрая разведка → основная работа"""
        
        logger.info("[Hybrid] Режим обхода: разведка через curl")
        
        # Быстрая проверка curl
        start = time.time()
        content = self.curl_parser.parse(url)
        elapsed = time.time() - start
        
        if content and len(content) > 100000:
            # curl получил полный контент
            if self._is_valid_content(content):
                logger.success(f"[Hybrid] curl справился ({elapsed:.1f}с)")
                self.stats['curl_success'] += 1
                self._show_stats()
                return content
        
        self.stats['curl_fail'] += 1
        
        # Основная работа через Playwright
        logger.info("[Hybrid] Активируем Playwright с антидетект")
        start = time.time()
        content = self.playwright_parser.parse(url)
        elapsed = time.time() - start
        
        if content:
            logger.success(f"[Hybrid] Playwright успешно ({elapsed:.1f}с)")
            self.stats['playwright_success'] += 1
        else:
            self.stats['playwright_fail'] += 1
        
        self._show_stats()
        return content
    
    def _is_valid_content(self, content: str) -> bool:
        """Проверка валидности контента"""
        if not content or len(content) < 20000:
            return False
        
        # Проверка на блокировку
        if self.check_blocking(content):
            return False
        
        # Проверка на наличие каталога Avito
        if "catalog-serp" not in content:
            logger.debug("[Hybrid] Каталог не найден в контенте")
            return False
        
        return True
    
    def _show_stats(self):
        """Показ статистики"""
        total = sum(self.stats.values())
        if total > 0:
            logger.debug(f"[Stats] curl: {self.stats['curl_success']}/{self.stats['curl_fail']} | "
                        f"playwright: {self.stats['playwright_success']}/{self.stats['playwright_fail']}")
```

### 4. core/local_parser.py
```python
from core.base_parser import BaseParser
from typing import Optional
from config.settings import settings, logger
import os

class LocalParser(BaseParser):
    """Парсер для локальных HTML файлов"""
    
    def parse(self, url: str = None) -> Optional[str]:
        """Читает HTML из локального файла"""
        
        filepath = settings.local_html_path
        
        if not filepath:
            logger.error("[Local] Не указан LOCAL_HTML_PATH в .env")
            return None
        
        if not os.path.exists(filepath):
            logger.error(f"[Local] Файл не найден: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.success(f"[Local] Загружен файл: {filepath}")
            logger.info(f"[Local] Размер: {len(content):,} байт")
            
            # Проверка контента
            if "catalog-serp" in content:
                logger.success("[Local] Каталог найден в файле")
            else:
                logger.warning("[Local] Каталог не найден в файле")
            
            return content
            
        except Exception as e:
            logger.error(f"[Local] Ошибка чтения: {e}")
            return None
```

### 5. Обновление core/playwright_parser.py
Добавьте в начало метода parse() после создания page:

```python
# Инжект stealth скрипта (если включен режим обхода)
stealth_script = antibot_toolkit.get_stealth_script()
if stealth_script:
    page.add_init_script(stealth_script)
    logger.debug("[Playwright] Stealth скрипт активирован")

# Эмуляция поведения (если включена)
if settings.use_antibot_tricks:
    # Случайная прокрутка
    page.evaluate("window.scrollTo(0, Math.random() * 500)")
    time.sleep(antibot_toolkit.get_random_delay())
```

### 6. Обновление main.py
```python
import sys
from config.settings import settings, logger
from core.playwright_parser import PlaywrightParser
from core.curl_parser import CurlParser
from core.hybrid_parser import HybridParser
from core.local_parser import LocalParser
from utils.file_manager import save_html

def get_parser(mode: str):
    """Фабрика парсеров (полная версия)"""
    
    # Локальный режим имеет приоритет
    if settings.use_local_html:
        logger.info("Режим: работа с локальным HTML")
        return LocalParser()
    
    # Выбор парсера
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
    logger.info("=== Avito Parser v2.0 (Full Version) ===")
    
    # Информация о режиме
    if settings.use_antibot_tricks:
        logger.warning("⚠️ РЕЖИМ ОБХОДА ЗАЩИТ ВКЛЮЧЕН")
        logger.warning("Используйте на свой риск!")
    else:
        logger.info("✅ Стандартный режим")
    
    # Проверка настроек
    if not settings.use_local_html and not settings.target_url:
        logger.error("Не задан TARGET_URL в .env")
        sys.exit(1)
    
    if not settings.use_local_html:
        logger.info(f"URL: {settings.target_url}")
    logger.info(f"Режим парсера: {settings.parser_mode}")
    
    # Получаем парсер
    parser = get_parser(settings.parser_mode)
    
    # Парсим
    try:
        if settings.use_local_html:
            html = parser.parse()  # LocalParser не требует URL
        else:
            html = parser.parse(settings.target_url)
        
        if html:
            # Сохраняем (если не локальный режим)
            if not settings.use_local_html:
                filepath = save_html(html, settings.target_url)
            else:
                filepath = settings.local_html_path
            
            # Анализ
            if "catalog-serp" in html:
                logger.success("✓ Каталог найден")
            elif self.check_blocking(html):
                logger.warning("⚠ Обнаружена блокировка")
                if not settings.use_antibot_tricks:
                    logger.info("Подсказка: попробуйте USE_ANTIBOT_TRICKS=true")
            else:
                logger.warning("⚠ Каталог не найден")
            
            # ПОЛНЫЙ вывод (как в Step 1)
            print("\n" + "="*50)
            print("ПОЛНЫЙ HTML:")
            print("="*50)
            print(html)
            print("="*50)
            print(f"Размер: {len(html):,} байт")
            if filepath:
                print(f"Файл: {filepath}")
            
        else:
            logger.error("Не удалось получить HTML")
            logger.info("Варианты решения:")
            logger.info("1. Изменить PARSER_MODE (curl/playwright/hybrid)")
            if not settings.use_antibot_tricks:
                logger.info("2. Включить USE_ANTIBOT_TRICKS=true")
            logger.info("3. Использовать локальный HTML (USE_LOCAL_HTML=true)")
            
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Проверка Playwright (если нужен)
    if settings.parser_mode in ["playwright", "hybrid"] and not settings.use_local_html:
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

## ТЕСТИРОВАНИЕ НОВЫХ ВОЗМОЖНОСТЕЙ

### Тест 1: curl парсер
```env
PARSER_MODE=curl
USE_ANTIBOT_TRICKS=false
```

### Тест 2: Гибридный режим
```env
PARSER_MODE=hybrid
USE_ANTIBOT_TRICKS=false
```

### Тест 3: Режим обхода защит
```env
PARSER_MODE=hybrid
USE_ANTIBOT_TRICKS=true
```

### Тест 4: Локальный HTML
```env
USE_LOCAL_HTML=true
LOCAL_HTML_PATH=trash/20241228_123456_www_avito_ru.html
```

---

## ПРОВЕРКА АПГРЕЙДА

✅ curl парсер работает и сохраняет cookies
✅ Гибридный режим переключается между парсерами
✅ Антибот техники включаются через .env
✅ Локальный парсер читает сохраненные HTML
✅ Статистика показывает эффективность методов

## ГОТОВАЯ АРХИТЕКТУРА

Теперь у вас полноценный парсер с:
- 3 типами парсеров (curl, playwright, hybrid)
- Опциональным обходом защит
- Работой с локальными файлами
- Умным переключением на основе контента
- Детальной статистикой

Это production-ready решение для образовательных целей!