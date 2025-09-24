import sqlite3
from typing import Optional
from config.settings import logger
from database.models import Listing
import json
import os

class DatabaseManager:
    """Управляет операциями с базой данных SQLite."""
    
    def __init__(self, db_path: str = "database/avito_listings.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_table()

    def _connect(self):
        """Устанавливает соединение с БД."""
        try:
            self._connection = sqlite3.connect(self.db_path)
            logger.debug(f"Успешное подключение к БД: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            self._connection = None

    def _create_table(self):
        """Создает таблицу для объявлений, если она не существует."""
        if not self._connection:
            return
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            price TEXT,
            address TEXT,
            description TEXT,
            images TEXT, -- Сохраняем как JSON-строку
            bail TEXT,
            tax TEXT,
            services TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            cursor = self._connection.cursor()
            cursor.execute(create_table_query)
            self._connection.commit()
            logger.debug("Таблица 'listings' готова к работе.")
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания таблицы: {e}")

    def add_listing(self, listing: Listing) -> bool:
        """Добавляет объявление в БД, избегая дубликатов по URL."""
        if not self._connection:
            logger.error("Нет подключения к БД.")
            return False
            
        # Проверка на дубликат
        if self._listing_exists(listing.url):
            logger.debug(f"Объявление уже существует: {listing.url}")
            return False

        insert_query = """
        INSERT INTO listings (url, title, price, address, description, images, bail, tax, services)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        images_json = json.dumps(listing.images)
        data = (
            listing.url, listing.title, listing.price, listing.address,
            listing.description, images_json, listing.bail, listing.tax, listing.services
        )

        try:
            cursor = self._connection.cursor()
            cursor.execute(insert_query, data)
            self._connection.commit()
            logger.debug(f"Добавлено новое объявление: {listing.title}")
            return True
        except sqlite3.IntegrityError:
            # На случай, если проверка _listing_exists не сработала
            logger.warning(f"Объявление уже существует (UNIQUE constraint): {listing.url}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Ошибка добавления объявления: {e}")
            return False

    def _listing_exists(self, url: str) -> bool:
        """Проверяет наличие объявления по URL."""
        if not self._connection:
            return False
        
        query = "SELECT 1 FROM listings WHERE url = ? LIMIT 1;"
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, (url,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Ошибка проверки существования объявления: {e}")
            return False
            
    def close(self):
        """Закрывает соединение с БД."""
        if self._connection:
            self._connection.close()
            logger.debug("Соединение с БД закрыто.")

    # === Дополнительные методы для Telegram-бота ===
    def get_listings_count(self) -> int:
        """Возвращает количество объектов в базе"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM listings")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Ошибка подсчета объектов: {e}")
            return 0

    def get_listings_page(self, page: int = 1, page_size: int = 5) -> list:
        """Возвращает страницу объектов"""
        offset = (page - 1) * page_size
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
            SELECT id, url, title, price, address, description
            FROM listings
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
                (page_size, offset),
            )

            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения страницы: {e}")
            return []

    def get_listing_by_id(self, listing_id: int) -> dict:
        """Возвращает объект по ID"""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM listings WHERE id = ?",
                (listing_id,),
            )
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения объекта {listing_id}: {e}")
            return None

    # Вспомогательный метод для кратковременных подключений
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

# Создаем единый экземпляр для всего приложения
db_manager = DatabaseManager()
