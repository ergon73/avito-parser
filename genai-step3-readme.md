Вы правы! Вот полноценный файл с пошаговыми инструкциями для Cursor:

# genai-step3-readme.md: Критические исправления и обход блокировок

## ТРЕБОВАНИЯ
✅ Step 2 завершен и работает
✅ Структура проекта сохранена  
✅ Установлен Google Chrome (не Chromium!)

## ЦЕЛЬ ЭТАПА 3
Исправить критические ошибки, выявленные экспертами, и внедрить новые техники обхода:
1. **Актуальные User-Agents 2025 года** (вместо устаревших 2022)
2. **Правильные HTTP/2 заголовки** (убрать запрещенные)
3. **Синхронизация TLS с User-Agent** (правильный impersonate)
4. **Улучшенная эмуляция поведения** человека
5. **Опциональное решение капч** через сервисы

---

## КРИТИЧЕСКАЯ ПРОБЛЕМА

Ваши текущие User-Agents устарели на 3 года (Chrome/104 вместо Chrome/140)! Это мгновенный детект для Avito.

---

## ШАГ 1: СОЗДАНИЕ НОВЫХ ПРОФИЛЕЙ

### 1.1 Создайте `services/browser_profiles_2025.py`
```python
"""
Актуальные профили браузеров на сентябрь 2025
КРИТИЧНО: Минимум заголовков, доверяем автогенерации
"""
import random

BROWSER_PROFILES = [
    # Chrome 140 на Windows - АКТУАЛЬНО на сентябрь 2025
    {
        "name": "Chrome Windows",
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        },
        "impersonate": "chrome",  # НЕ chrome120! Автовыбор последней версии
        "viewport": {"width": 1920, "height": 1080},
        "platform": "windows"
    },
    # Chrome на macOS
    {
        "name": "Chrome macOS", 
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        },
        "impersonate": "chrome",
        "viewport": {"width": 1440, "height": 900},
        "platform": "mac"
    },
    # Firefox 143 на Windows - АКТУАЛЬНО на сентябрь 2025
    {
        "name": "Firefox Windows",
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0",
            # НЕТ Connection: keep-alive! Запрещен в HTTP/2
        },
        "impersonate": "firefox",  # НЕ firefox110!
        "viewport": {"width": 1920, "height": 1080},
        "platform": "windows"
    },
    # Safari 18 на macOS
    {
        "name": "Safari macOS",
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "ru-RU",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        },
        "impersonate": "safari",
        "viewport": {"width": 1440, "height": 900},
        "platform": "mac"
    },
    # Edge 140 на Windows
    {
        "name": "Edge Windows",
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        },
        "impersonate": "edge",
        "viewport": {"width": 1920, "height": 1080},
        "platform": "windows"
    }
]

# КРИТИЧНО: НЕ добавляем эти заголовки - они автогенерируются:
# - sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform (GREASE-рандомизация) 
# - sec-fetch-dest, sec-fetch-mode, sec-fetch-site (контекстные)
# - connection, cache-control (управляются браузером)

def get_random_profile():
    """Возвращает случайный профиль"""
    return random.choice(BROWSER_PROFILES)

def get_profile_by_name(name):
    """Возвращает профиль по имени"""
    for profile in BROWSER_PROFILES:
        if profile["name"] == name:
            return profile
    return BROWSER_PROFILES[0]
```

---

## ШАГ 2: ОБНОВЛЕНИЕ CURL ПАРСЕРА

### 2.1 Замените метод parse в `core/curl_parser.py`
```python
def parse(self, url: str) -> Optional[str]:
    """Загрузка через curl-cffi с актуальными профилями"""
    
    # Используем новые профили 2025 года
    from services.browser_profiles_2025 import get_random_profile
    profile = get_random_profile()
    
    headers = profile["headers"].copy()
    impersonate = profile["impersonate"]  # Теперь это алиас: chrome/firefox/safari
    
    logger.info(f"[curl] Используем профиль: {profile['name']}")
    logger.debug(f"[curl] Impersonate: {impersonate}")
    
    for attempt in range(3):
        try:
            # КРИТИЧНО: используем правильный impersonate
            response = self.session.get(
                url,
                headers=headers,
                impersonate=impersonate,  # curl-cffi сам выберет актуальную версию
                timeout=30,
                allow_redirects=True,
                verify=True  # Проверка SSL важна
            )
            
            self._save_cookies()
            content = response.text
            
            if response.status_code == 429:
                logger.warning(f"[curl] HTTP 429 - слишком много запросов")
                if attempt < 2:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"[curl] Ждем {wait_time} секунд...")
                    time.sleep(wait_time)
                    continue
            
            if self.check_blocking(content):
                logger.warning(f"[curl] Обнаружена блокировка (попытка {attempt + 1}/3)")
                if attempt < 2:
                    time.sleep(random.uniform(3, 7))
                    continue
            
            logger.success(f"[curl] Получено {len(content):,} байт")
            return content
            
        except Exception as e:
            logger.error(f"[curl] Ошибка (попытка {attempt + 1}/3): {e}")
            if attempt < 2:
                time.sleep(3)
    
    return None
```

---

## ШАГ 3: КРИТИЧЕСКОЕ ОБНОВЛЕНИЕ PLAYWRIGHT

### 3.1 Полностью замените `core/playwright_parser.py`
```python
from core.base_parser import BaseParser
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from typing import Optional
from loguru import logger
import random
import time
import os

class PlaywrightParser(BaseParser):
    """Парсер с использованием настоящего Chrome и улучшенной маскировкой"""
    
    def parse(self, url: str) -> Optional[str]:
        """Загружает страницу с эмуляцией реального пользователя"""
        
        # Используем новые профили
        from services.browser_profiles_2025 import get_random_profile
        profile = get_random_profile()
        
        logger.info(f"[Playwright] Используем профиль: {profile['name']}")
        
        # Определяем режим браузера из .env
        use_headless = os.getenv("USE_HEADLESS", "false").lower() == "true"
        browser_channel = os.getenv("BROWSER_CHANNEL", "chrome")
        
        try:
            with sync_playwright() as p:
                # КРИТИЧНО: Пробуем настоящий Chrome
                browser = None
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    f'--user-agent={profile["headers"]["user-agent"]}'
                ]
                
                if browser_channel == "chrome" and not use_headless:
                    try:
                        # Используем установленный Google Chrome
                        browser = p.chromium.launch(
                            headless=False,
                            channel="chrome",
                            args=browser_args
                        )
                        logger.success("[Playwright] Используется Google Chrome (не headless)")
                    except Exception as e:
                        logger.warning(f"[Playwright] Chrome недоступен: {e}")
                
                if not browser:
                    # Fallback на Chromium
                    browser = p.chromium.launch(
                        headless=use_headless,
                        args=browser_args
                    )
                    mode = "headless" if use_headless else "headed"
                    logger.info(f"[Playwright] Используется Chromium ({mode})")
                
                # Создаем контекст с минимумом заголовков
                context = browser.new_context(
                    user_agent=profile["headers"]["user-agent"],
                    viewport=profile["viewport"],
                    locale='ru-RU',
                    timezone_id='Europe/Moscow',
                    # ВАЖНО: передаем только accept-language, остальное генерируется
                    extra_http_headers={
                        'accept-language': profile["headers"]["accept-language"]
                    },
                    # Дополнительные параметры для реалистичности
                    device_scale_factor=1.0,
                    has_touch=False,
                    is_mobile=False
                )
                
                # Добавляем cookies если есть
                self._load_cookies(context)
                
                page = context.new_page()
                
                # Применяем улучшенный stealth перед навигацией
                self._apply_stealth(page)
                
                # Эмулируем поведение до перехода
                self._pre_navigation_behavior(page)
                
                logger.info(f"[Playwright] Переход на {url}")
                
                # Навигация с реалистичным ожиданием
                response = page.goto(
                    url,
                    wait_until='domcontentloaded',  # Не ждем networkidle - слишком долго
                    timeout=60000
                )
                
                if response and response.status == 429:
                    logger.error("[Playwright] HTTP 429 - Rate limit")
                    browser.close()
                    return None
                
                # Эмулируем поведение после загрузки
                self._post_navigation_behavior(page)
                
                # Проверяем наличие каталога
                try:
                    page.wait_for_selector("div[data-marker='catalog-serp']", timeout=15000)
                    logger.success("[Playwright] Каталог найден")
                except PlaywrightTimeoutError:
                    logger.warning("[Playwright] Каталог не найден - возможна блокировка")
                    # Проверяем на капчу
                    if page.query_selector("iframe[src*='hcaptcha']"):
                        logger.warning("[Playwright] Обнаружена hCaptcha")
                    elif page.query_selector("div.geetest_captcha"):
                        logger.warning("[Playwright] Обнаружена GeeTest Captcha")
                
                # Дополнительное ожидание
                page.wait_for_timeout(random.randint(2000, 4000))
                
                content = page.content()
                
                # Сохраняем cookies
                self._save_cookies(context)
                
                browser.close()
                
                logger.success(f"[Playwright] Получено {len(content):,} байт")
                return content
                
        except PlaywrightTimeoutError:
            logger.error("[Playwright] Timeout загрузки")
            return None
        except Exception as e:
            logger.error(f"[Playwright] Ошибка: {e}")
            if "Executable not found" in str(e):
                logger.error("Выполните: playwright install chromium")
            return None
    
    def _apply_stealth(self, page):
        """Применяет продвинутые техники маскировки"""
        stealth_js = """
        // Убираем webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Правильные плагины для Chrome
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {0: {type: "application/x-google-chrome-pdf", suffixes: "pdf"}},
                {0: {type: "application/pdf", suffixes: "pdf"}}
            ]
        });
        
        // Правильный chrome объект
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {}
        };
        
        // Исправляем permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        page.add_init_script(stealth_js)
        logger.debug("[Playwright] Stealth скрипт применен")
    
    def _pre_navigation_behavior(self, page):
        """Эмулирует поведение перед переходом"""
        try:
            # Движение мыши от края
            page.mouse.move(0, 0)
            time.sleep(random.uniform(0.1, 0.3))
            page.mouse.move(
                random.randint(400, 800),
                random.randint(200, 400),
                steps=random.randint(10, 20)
            )
            logger.debug("[Playwright] Pre-navigation поведение выполнено")
        except Exception as e:
            logger.debug(f"[Playwright] Pre-navigation ошибка: {e}")
    
    def _post_navigation_behavior(self, page):
        """Эмулирует поведение после загрузки"""
        try:
            # Человеческая пауза
            time.sleep(random.uniform(1.5, 3.0))
            
            # Случайные скроллы
            for _ in range(random.randint(1, 3)):
                scroll_y = random.randint(100, 300)
                page.evaluate(f"window.scrollBy(0, {scroll_y})")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Движение мыши над элементами
            page.mouse.move(
                random.randint(300, 700),
                random.randint(200, 500),
                steps=random.randint(5, 10)
            )
            
            logger.debug("[Playwright] Post-navigation поведение выполнено")
        except Exception as e:
            logger.debug(f"[Playwright] Post-navigation ошибка: {e}")
    
    def _load_cookies(self, context):
        """Загружает сохраненные cookies"""
        cookies_file = "cookies/playwright_cookies.json"
        if os.path.exists(cookies_file):
            try:
                import json
                with open(cookies_file, 'r') as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    logger.debug("[Playwright] Cookies загружены")
            except Exception as e:
                logger.debug(f"[Playwright] Ошибка загрузки cookies: {e}")
    
    def _save_cookies(self, context):
        """Сохраняет cookies"""
        try:
            import json
            os.makedirs("cookies", exist_ok=True)
            cookies = context.cookies()
            with open("cookies/playwright_cookies.json", 'w') as f:
                json.dump(cookies, f)
            logger.debug("[Playwright] Cookies сохранены")
        except Exception as e:
            logger.debug(f"[Playwright] Ошибка сохранения cookies: {e}")
```

---

## ШАГ 4: ОБНОВЛЕНИЕ ГИБРИДНОГО ПАРСЕРА

### 4.1 Обновите `core/hybrid_parser.py`
Добавьте в начало метода parse:
```python
def parse(self, url: str) -> Optional[str]:
    """Умное переключение между парсерами с новыми профилями"""
    
    # Загружаем новые профили
    from services.browser_profiles_2025 import BROWSER_PROFILES
    logger.info(f"[Hybrid] Доступно {len(BROWSER_PROFILES)} актуальных профилей")
    
    # ... остальной код
```

---

## ШАГ 5: ОБНОВЛЕНИЕ .env.example

### 5.1 Замените содержимое `.env.example`
```env
# === ОСНОВНЫЕ НАСТРОЙКИ ===
TARGET_URL=https://www.avito.ru/city/kvartiry/sdam/na_dlitelnyy_srok
PARSER_MODE=hybrid
LOG_LEVEL=INFO

# === РЕЖИМЫ РАБОТЫ ===
USE_ANTIBOT_TRICKS=true
USE_LOCAL_HTML=false
LOCAL_HTML_PATH=trash/avito_page.html

# === НОВОЕ В STEP 3 ===
# Режим браузера
USE_HEADLESS=false  # false = видимый браузер (рекомендуется для начала)
BROWSER_CHANNEL=chrome  # chrome/chromium/msedge

# Решение капч (опционально)
ENABLE_CAPTCHA_SOLVING=false
CAPTCHA_API_KEY=  # Ключ от 2captcha.com или anti-captcha.com

# === БУДУЩИЕ РАСШИРЕНИЯ ===
USE_PROXY=false
PROXY_URL=
PROXY_USERNAME=
PROXY_PASSWORD=

# Ротация профилей
ROTATE_PROFILES=true
PREFERRED_PROFILE=  # Chrome Windows / Firefox Windows / Safari macOS
```

---

## ШАГ 6: ТЕСТИРОВАНИЕ

### 6.1 Создайте тестовый скрипт `test_step3.py`
```python
#!/usr/bin/env python3
"""Тестирование Step 3 улучшений"""

from config.settings import settings, logger
from services.browser_profiles_2025 import BROWSER_PROFILES
import sys

def test_profiles():
    """Проверка новых профилей"""
    logger.info("=== ТЕСТ ПРОФИЛЕЙ 2025 ===")
    
    for i, profile in enumerate(BROWSER_PROFILES, 1):
        logger.info(f"{i}. {profile['name']}")
        logger.info(f"   UA: {profile['headers']['user-agent'][:50]}...")
        logger.info(f"   Impersonate: {profile['impersonate']}")
        
        # Проверка критических ошибок
        if "chrome120" in str(profile.get("impersonate")):
            logger.error("   ⚠️ ОШИБКА: Устаревший impersonate!")
        if "connection" in profile["headers"]:
            logger.error("   ⚠️ ОШИБКА: Запрещенный заголовок Connection!")
        if "sec-ch-ua" in profile["headers"]:
            logger.warning("   ⚠️ Предупреждение: sec-ch-ua не должен быть хардкодным")

def test_chrome_availability():
    """Проверка доступности Google Chrome"""
    logger.info("\n=== ТЕСТ CHROME ===")
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome", headless=False)
                browser.close()
                logger.success("✅ Google Chrome доступен!")
            except:
                logger.warning("⚠️ Google Chrome не найден, будет использован Chromium")
    except Exception as e:
        logger.error(f"❌ Playwright ошибка: {e}")

def main():
    logger.info("=== AVITO PARSER STEP 3 - ДИАГНОСТИКА ===\n")
    
    # Тест 1: Профили
    test_profiles()
    
    # Тест 2: Chrome
    test_chrome_availability()
    
    # Тест 3: Основная проверка
    logger.info("\n=== РЕКОМЕНДАЦИИ ===")
    logger.info("1. Установите Google Chrome если его нет")
    logger.info("2. Начните с USE_HEADLESS=false чтобы видеть процесс")
    logger.info("3. Попробуйте разные профили через PREFERRED_PROFILE")
    logger.info("4. Если блокировка продолжается - используйте прокси")
    
if __name__ == "__main__":
    main()
```

---

## ПОРЯДОК ВНЕДРЕНИЯ

1. **Создайте все новые файлы** из инструкций выше
2. **Обновите существующие файлы** согласно инструкциям
3. **Запустите диагностику**: `python test_step3.py`
4. **Проверьте .env** - установите `USE_HEADLESS=false`
5. **Запустите парсер**: `python main.py`

## ПРОВЕРОЧНЫЙ ЧЕКЛИСТ

✅ Новые User-Agents версии 140+ (не 104!)
✅ Правильный impersonate ("chrome", не "chrome120") 
✅ Нет заголовка Connection в Firefox профиле
✅ Нет хардкодных sec-ch-ua заголовков
✅ Google Chrome установлен (проверьте!)
✅ USE_HEADLESS=false для начального теста

## ЕСЛИ ВСЕ ЕЩЕ БЛОКИРОВКА

1. **Попробуйте Safari профиль** - часто работает лучше
2. **Увеличьте паузы** между запросами
3. **Используйте прокси** (residential, не datacenter)
4. **Рассмотрите платные решения**:
   - ScrapingBee ($49/месяц)
   - Bright Data (от $500/месяц)
   - 2captcha для решения капч ($3 за 1000)

## ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ

Эти улучшения значительно повышают шансы, но Avito использует Machine Learning для детекции. 100% гарантии нет. Для production используйте официальные API или платные сервисы.