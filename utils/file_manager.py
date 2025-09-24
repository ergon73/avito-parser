import os
from datetime import datetime
from loguru import logger
from urllib.parse import urlparse

def save_html(content: str, url: str, folder: str = "trash") -> str:
    """Сохраняет HTML в файл"""
    
    if not content:
        logger.warning("Нет контента для сохранения")
        return None
    
    # Создаем папку
    os.makedirs(folder, exist_ok=True)
    
    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = urlparse(url).netloc.replace('.', '_')
    filename = f"{timestamp}_{domain}.html"
    filepath = os.path.join(folder, filename)
    
    # Сохраняем
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.success(f"Сохранено: {filepath} ({len(content):,} байт)")
        return filepath
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return None
