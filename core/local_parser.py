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
