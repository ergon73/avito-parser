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
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml',
                'accept-language': 'ru-RU,ru;q=0.9',
                'user-agent': data_manager.get_random_user_agent()
            }
            logger.debug(f"[Antibot] Стандартные headers: {len(headers)} заголовков")
            return headers
        
        # Режим обхода - полный набор + рандомизация
        headers = data_manager.headers.copy()
        headers['user-agent'] = data_manager.get_random_user_agent()
        
        # Добавляем случайные заголовки
        if random.random() > 0.5:
            headers['referer'] = 'https://www.google.com/'
        
        logger.debug(f"[Antibot] Расширенные headers: {len(headers)} заголовков")
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
