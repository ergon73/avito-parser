from core.base_parser import BaseParser
from curl_cffi import requests
from typing import Optional
from services.antibot_toolkit import antibot_toolkit
from config.settings import settings, logger
import json
import os
import time

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
        try:
            for cookie in self.session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path
                })
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
        except Exception as e:
            logger.debug(f"[curl] Ошибка сохранения cookies: {e}")
    
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
