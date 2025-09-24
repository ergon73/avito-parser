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