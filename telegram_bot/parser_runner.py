"""
Интеграция с парсером - безопасный запуск в потоке
"""
import threading
import time
from pathlib import Path
import sys
from loguru import logger

# Добавляем корневую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent.parent))

from database.database_manager import DatabaseManager
from core.playwright_parser import PlaywrightParser
from services.avito_processor import AvitoProcessor
from config.settings import settings


class ParserRunner:
    def __init__(self):
        self.is_running = False
        self.last_run = None
        self.last_result = None

    def run_parser(self, callback=None):
        """
        Запускает парсер в отдельном потоке
        callback(status, message) - функция для отправки статуса в бот
        """
        if self.is_running:
            return {"success": False, "error": "Парсер уже работает"}

        def _run():
            self.is_running = True
            start_time = time.time()

            try:
                if callback:
                    callback("started", "🚀 Парсер запущен, загружаю страницу...")

                db = DatabaseManager()
                count_before = db.get_listings_count() if hasattr(db, 'get_listings_count') else 0

                parser = PlaywrightParser()
                url = settings.target_url
                html = parser.parse(url)

                if not html:
                    raise Exception("Не удалось загрузить страницу (возможна блокировка)")

                if callback:
                    callback("processing", "📝 Обрабатываю данные...")

                processor = AvitoProcessor(settings.target_url)
                listings = processor.process_html(html)

                added = 0
                for listing in listings:
                    if db.add_listing(listing):
                        added += 1

                count_after = db.get_listings_count() if hasattr(db, 'get_listings_count') else 0
                elapsed = round(time.time() - start_time, 1)

                self.last_run = time.time()
                self.last_result = {
                    "success": True,
                    "found": len(listings),
                    "added": added,
                    "total": count_after,
                    "elapsed": elapsed
                }

                if callback:
                    message = (
                        f"✅ <b>Парсинг завершен</b>\n\n"
                        f"📦 Найдено: {len(listings)}\n"
                        f"➕ Добавлено новых: {added}\n"
                        f"📊 Всего в базе: {count_after}\n"
                        f"⏱ Время: {elapsed} сек"
                    )
                    callback("completed", message)

            except Exception as e:
                logger.error(f"Ошибка парсинга: {e}")
                self.last_result = {
                    "success": False,
                    "error": str(e)
                }
                if callback:
                    error_msg = str(e)
                    if "429" in error_msg or "rate" in error_msg.lower():
                        message = (
                            "⚠️ <b>Avito временно заблокировал доступ</b>\n\n"
                            "Это происходит при частых запросах.\n"
                            "Попробуйте через 10-15 минут или используйте VPN."
                        )
                    else:
                        message = f"❌ Ошибка парсинга:\n<code>{error_msg[:200]}</code>"
                    callback("error", message)
            finally:
                self.is_running = False

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return {"success": True, "message": "Парсер запущен"}

    def get_status(self):
        """Возвращает статус парсера"""
        db = DatabaseManager()
        total = db.get_listings_count() if hasattr(db, 'get_listings_count') else 0

        status = "🟢 Работает" if self.is_running else "⏸ Ожидает"

        last_run_text = "Никогда"
        if self.last_run:
            minutes_ago = int((time.time() - self.last_run) / 60)
            if minutes_ago < 1:
                last_run_text = "Только что"
            elif minutes_ago < 60:
                last_run_text = f"{minutes_ago} мин. назад"
            else:
                hours = minutes_ago // 60
                last_run_text = f"{hours} ч. назад"

        return {
            "status": status,
            "total": total,
            "last_run": last_run_text,
            "is_running": self.is_running
        }


# Глобальный экземпляр
parser_runner = ParserRunner()


