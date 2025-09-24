import sys
from config.settings import settings, logger
from core.playwright_parser import PlaywrightParser
from core.curl_parser import CurlParser
from core.hybrid_parser import HybridParser
from core.local_parser import LocalParser
from services.avito_processor import AvitoProcessor
from database.database_manager import db_manager

def get_parser(mode: str):
    """Фабрика парсеров (полная версия)"""
    if settings.use_local_html:
        logger.info("Режим: работа с локальным HTML")
        return LocalParser()
    
    if mode == "playwright":
        return PlaywrightParser()
    elif mode == "curl":
        return CurlParser()
    elif mode == "hybrid":
        return HybridParser()
    else:
        logger.warning(f"Неизвестный режим {mode}, используем playwright")
        return PlaywrightParser()

def main():
    logger.info("=== Avito Parser v3.0 (Data & Docker) ===")
    
    if settings.use_antibot_tricks:
        logger.warning("⚠️ РЕЖИМ ОБХОДА ЗАЩИТ ВКЛЮЧЕН")
    else:
        logger.info("✅ Стандартный режим")
    
    if not settings.use_local_html and not settings.target_url:
        logger.error("Не задан TARGET_URL в .env")
        sys.exit(1)
    
    # 1. ПОЛУЧЕНИЕ HTML
    parser = get_parser(settings.parser_mode)
    try:
        url = None if settings.use_local_html else settings.target_url
        html = parser.parse(url)
        
        if not html:
            logger.error("Не удалось получить HTML. Завершение работы.")
            sys.exit(1)
            
        # 2. ОБРАБОТКА HTML И ИЗВЛЕЧЕНИЕ ДАННЫХ
        logger.info("Начало обработки HTML...")
        processor = AvitoProcessor(base_url=settings.target_url)
        listings = processor.process_html(html)
        
        if not listings:
            logger.warning("Не удалось извлечь ни одного объявления. Проверьте селекторы в avito_processor.py")
            sys.exit(0)
            
        # 3. СОХРАНЕНИЕ В БАЗУ ДАННЫХ
        added_count = 0
        for listing in listings:
            if db_manager.add_listing(listing):
                added_count += 1
        
        logger.success("="*50)
        logger.success(f"         ОБРАБОТКА ЗАВЕРШЕНА")
        logger.success(f"  Всего найдено на странице: {len(listings)}")
        logger.success(f"  Новых добавлено в БД: {added_count}")
        logger.success("="*50)
        
    except Exception as e:
        logger.exception(f"Критическая ошибка в главном цикле: {e}")
        sys.exit(1)
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()
