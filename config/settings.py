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
logger.add("logs/app.log", level="DEBUG", rotation="10 MB", 
           format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}")
