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
