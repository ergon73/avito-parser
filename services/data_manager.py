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
