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
        logger.debug(f"[Hybrid] Проверка контента: {len(content):,} байт")
        
        if not content or len(content) < 20000:
            logger.debug(f"[Hybrid] Контент слишком короткий: {len(content) if content else 0} байт")
            return False
        
        # Проверка на блокировку
        if self.check_blocking(content):
            logger.debug("[Hybrid] Обнаружена блокировка в контенте")
            return False
        
        # Проверка на наличие каталога Avito
        if "catalog-serp" not in content:
            logger.debug("[Hybrid] Каталог не найден в контенте")
            # Дополнительная диагностика
            if "Доступ ограничен" in content:
                logger.debug("[Hybrid] Страница блокировки обнаружена")
            elif "captcha" in content.lower():
                logger.debug("[Hybrid] Капча обнаружена")
            return False
        
        logger.debug("[Hybrid] Контент валиден")
        return True
    
    def _show_stats(self):
        """Показ статистики"""
        total = sum(self.stats.values())
        if total > 0:
            logger.debug(f"[Stats] curl: {self.stats['curl_success']}/{self.stats['curl_fail']} | "
                        f"playwright: {self.stats['playwright_success']}/{self.stats['playwright_fail']}")
