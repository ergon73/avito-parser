# genai-step5-readme.md: Интеграция Telegram-бота с парсером Avito

## Обзор архитектуры

Добавляем Telegram-бота как независимый модуль, который управляет существующим парсером через API-вызовы. Бот не меняет структуру парсера, а только вызывает его функции.

```
VB-INTENSIV/
├── telegram_bot/          # НОВЫЙ МОДУЛЬ
│   ├── __init__.py
│   ├── bot.py           # Главный файл бота
│   ├── handlers.py      # Обработчики команд
│   ├── keyboards.py     # Клавиатуры
│   ├── parser_runner.py # Интеграция с парсером
│   └── utils.py         # Вспомогательные функции
├── core/                 # Существующий парсер
├── database/            
├── ...
└── .env                  # + токен бота
```

---

## ШАГ 1: Подготовка окружения

### 1.1 Обновите requirements.txt
```txt
# Добавьте в конец файла
pyTelegramBotAPI>=4.14.0
APScheduler>=3.10.4
```

### 1.2 Добавьте в .env
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
TELEGRAM_ADMIN_ID=YOUR_TELEGRAM_ID  # Опционально для уведомлений
```

### 1.3 Создайте структуру telegram_bot
```bash
mkdir telegram_bot
touch telegram_bot/__init__.py
```

---

## ШАГ 2: Основные файлы бота

### 2.1 telegram_bot/keyboards.py
```python
"""
Клавиатуры для Telegram-бота
"""
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    """Главное меню бота"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 Статус парсера", callback_data="status"),
        InlineKeyboardButton("📖 Журнал объектов", callback_data="journal:1")
    )
    markup.add(
        InlineKeyboardButton("🚀 Запустить парсер", callback_data="run_parser"),
        InlineKeyboardButton("🔍 Поиск", callback_data="search")
    )
    markup.add(
        InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        InlineKeyboardButton("📈 Статистика", callback_data="stats")
    )
    return markup

def journal_navigation(current_page, total_pages, listings):
    """Навигация по журналу с кнопками объектов"""
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Кнопки для каждого объекта
    for listing in listings:
        btn_text = f"🏠 {listing['title'][:40]}... - {listing['price']}"
        markup.add(InlineKeyboardButton(
            btn_text, 
            callback_data=f"view:{listing['id']}:{current_page}"
        ))
    
    # Навигация
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"journal:{current_page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(
        f"{current_page}/{total_pages}", 
        callback_data="noop"
    ))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"journal:{current_page+1}"))
    
    if nav_buttons:
        markup.add(*nav_buttons)
    
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data="menu"))
    return markup

def listing_details(listing_id, page, url):
    """Кнопки для детальной карточки"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔗 Открыть на Avito", url=url),
        InlineKeyboardButton("🔙 Назад к списку", callback_data=f"back_journal:{page}")
    )
    return markup

def settings_menu():
    """Меню настроек"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔄 Автозапуск", callback_data="autorun_menu"),
        InlineKeyboardButton("📝 Изменить URL", callback_data="change_url"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )
    return markup
```

### 2.2 telegram_bot/parser_runner.py
```python
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
                # Уведомляем о начале
                if callback:
                    callback("started", "🚀 Парсер запущен, загружаю страницу...")
                
                # Считаем объекты до парсинга
                db = DatabaseManager()
                count_before = db.get_listings_count()
                
                # Запускаем парсер
                parser = PlaywrightParser()
                html = parser.parse(settings.target_url)
                
                if not html:
                    raise Exception("Не удалось загрузить страницу (возможна блокировка)")
                
                if callback:
                    callback("processing", "📝 Обрабатываю данные...")
                
                # Обрабатываем данные
                processor = AvitoProcessor(settings.target_url)
                listings = processor.process_html(html)
                
                # Сохраняем в БД
                added = 0
                for listing in listings:
                    if db.add_listing(listing):
                        added += 1
                
                # Считаем после
                count_after = db.get_listings_count()
                elapsed = round(time.time() - start_time, 1)
                
                self.last_run = time.time()
                self.last_result = {
                    "success": True,
                    "found": len(listings),
                    "added": added,
                    "total": count_after,
                    "elapsed": elapsed
                }
                
                # Уведомляем о завершении
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
        total = db.get_listings_count()
        
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
```

### 2.3 telegram_bot/handlers.py
```python
"""
Обработчики команд и колбэков
"""
import json
from loguru import logger
from database.database_manager import DatabaseManager
from .keyboards import *
from .parser_runner import parser_runner

ITEMS_PER_PAGE = 5

def register_handlers(bot):
    """Регистрирует все обработчики"""
    
    @bot.message_handler(commands=['start'])
    def cmd_start(message):
        welcome_text = (
            "👋 <b>Добро пожаловать в Avito Parser Bot!</b>\n\n"
            "Я помогу вам отслеживать объявления на Avito.\n\n"
            "Выберите действие:"
        )
        bot.send_message(
            message.chat.id, 
            welcome_text,
            reply_markup=main_menu(),
            parse_mode='HTML'
        )
    
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        data = call.data
        
        try:
            # Главное меню
            if data == "menu":
                bot.edit_message_text(
                    "📋 <b>Главное меню</b>\n\nВыберите действие:",
                    chat_id, message_id,
                    reply_markup=main_menu(),
                    parse_mode='HTML'
                )
                
            # Статус парсера
            elif data == "status":
                status = parser_runner.get_status()
                text = (
                    f"📊 <b>Статус парсера</b>\n\n"
                    f"Состояние: {status['status']}\n"
                    f"Объектов в базе: {status['total']}\n"
                    f"Последний запуск: {status['last_run']}"
                )
                
                markup = InlineKeyboardMarkup()
                if not status['is_running']:
                    markup.add(InlineKeyboardButton("🚀 Запустить", callback_data="run_parser"))
                markup.add(InlineKeyboardButton("🔙 Назад", callback_data="menu"))
                
                bot.edit_message_text(
                    text, chat_id, message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            
            # Журнал объектов
            elif data.startswith("journal:"):
                page = int(data.split(":")[1])
                show_journal(bot, chat_id, message_id, page)
            
            # Просмотр объекта
            elif data.startswith("view:"):
                parts = data.split(":")
                listing_id = int(parts[1])
                page = int(parts[2])
                show_listing_details(bot, chat_id, listing_id, page)
                
            # Возврат к журналу (с удалением карточки)
            elif data.startswith("back_journal:"):
                page = int(data.split(":")[1])
                bot.delete_message(chat_id, message_id)
                
                # Отправляем новое сообщение с журналом
                msg = bot.send_message(chat_id, "Загружаю журнал...")
                show_journal(bot, chat_id, msg.message_id, page)
            
            # Запуск парсера
            elif data == "run_parser":
                if parser_runner.is_running:
                    bot.answer_callback_query(call.id, "⚠️ Парсер уже работает!", show_alert=True)
                else:
                    bot.answer_callback_query(call.id, "🚀 Запускаю парсер...")
                    
                    def callback(status, message):
                        """Отправляет обновления статуса"""
                        if status == "started":
                            bot.edit_message_text(message, chat_id, message_id, parse_mode='HTML')
                        else:
                            try:
                                bot.delete_message(chat_id, message_id)
                            except:
                                pass
                            bot.send_message(chat_id, message, parse_mode='HTML')
                    
                    result = parser_runner.run_parser(callback)
                    if not result['success']:
                        bot.answer_callback_query(call.id, result['error'], show_alert=True)
            
            # Настройки
            elif data == "settings":
                bot.edit_message_text(
                    "⚙️ <b>Настройки</b>",
                    chat_id, message_id,
                    reply_markup=settings_menu(),
                    parse_mode='HTML'
                )
            
            # Заглушки
            elif data in ["search", "stats", "autorun_menu", "change_url"]:
                bot.answer_callback_query(
                    call.id, 
                    "🚧 Эта функция будет доступна в следующей версии",
                    show_alert=True
                )
            
            elif data == "noop":
                bot.answer_callback_query(call.id)
                
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            bot.answer_callback_query(call.id, "Произошла ошибка", show_alert=True)

def show_journal(bot, chat_id, message_id, page=1):
    """Отображает журнал объектов"""
    db = DatabaseManager()
    total = db.get_listings_count()
    
    if total == 0:
        bot.edit_message_text(
            "📖 <b>Журнал пуст</b>\n\nЗапустите парсер для получения данных.",
            chat_id, message_id,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🚀 Запустить парсер", callback_data="run_parser"),
                InlineKeyboardButton("🔙 В меню", callback_data="menu")
            ),
            parse_mode='HTML'
        )
        return
    
    # Получаем страницу
    listings = db.get_listings_page(page, ITEMS_PER_PAGE)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    text = f"📖 <b>Журнал объектов</b>\nСтраница {page}/{total_pages}\n\n"
    
    bot.edit_message_text(
        text + "Выберите объект для просмотра:",
        chat_id, message_id,
        reply_markup=journal_navigation(page, total_pages, listings),
        parse_mode='HTML'
    )

def show_listing_details(bot, chat_id, listing_id, page):
    """Показывает детали объекта в новом сообщении"""
    db = DatabaseManager()
    listing = db.get_listing_by_id(listing_id)
    
    if not listing:
        bot.answer_callback_query(chat_id, "Объект не найден", show_alert=True)
        return
    
    # Формируем текст
    text = f"🏠 <b>{listing['title']}</b>\n\n"
    
    if listing['price']:
        text += f"💰 Цена: <b>{listing['price']}</b>\n"
    if listing['address']:
        text += f"📍 Адрес: {listing['address']}\n"
    if listing['description']:
        desc = listing['description'][:500]
        if len(listing['description']) > 500:
            desc += "..."
        text += f"\n📝 Описание:\n{desc}\n"
    
    # Отправляем новое сообщение с деталями
    bot.send_message(
        chat_id,
        text,
        reply_markup=listing_details(listing_id, page, listing['url']),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
```

### 2.4 telegram_bot/bot.py
```python
#!/usr/bin/env python3
"""
Главный файл Telegram-бота
"""
import os
import sys
from pathlib import Path
from loguru import logger
import telebot
from telebot import apihelper

# Добавляем корень проекта в путь
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings
from telegram_bot.handlers import register_handlers

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | {level} | <cyan>BOT</cyan> | {message}",
    level="INFO"
)

def main():
    """Точка входа бота"""
    
    # Получаем токен из настроек
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("telegram_bot_token")
    
    if not token:
        logger.error("❌ Не найден TELEGRAM_BOT_TOKEN в .env файле!")
        logger.info("Добавьте в .env: TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather")
        sys.exit(1)
    
    # Создаем бота
    bot = telebot.TeleBot(token, parse_mode='HTML')
    
    # Регистрируем обработчики
    register_handlers(bot)
    
    logger.success("✅ Avito Parser Bot запущен!")
    logger.info("Нажмите Ctrl+C для остановки")
    
    try:
        bot.polling(none_stop=True, interval=1)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## ШАГ 3: Интеграция с базой данных

### 3.1 Дополните database/database_manager.py
```python
# Добавьте эти методы в класс DatabaseManager

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
        cursor.execute("""
            SELECT id, url, title, price, address, description
            FROM listings
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        
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
            (listing_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Ошибка получения объекта {listing_id}: {e}")
        return None
```

---

## ШАГ 4: Docker интеграция

### 4.1 Обновите docker-compose.yml
```yaml
version: '3.8'

services:
  avito-parser-bot:
    build: .
    container_name: avito-parser-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./database:/app/database
      - ./logs:/app/logs
      - ./trash:/app/trash
    command: python telegram_bot/bot.py
    networks:
      - parser-network

networks:
  parser-network:
    driver: bridge
```

### 4.2 Создайте скрипт запуска run_bot.sh
```bash
#!/bin/bash
# Скрипт для локального запуска бота

# Активируем виртуальное окружение если есть
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Устанавливаем зависимости если нужно
pip install -q pyTelegramBotAPI

# Запускаем бота
python telegram_bot/bot.py
```

---

## ШАГ 5: Тестирование

### 5.1 Локальный запуск
```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите бота
python telegram_bot/bot.py
```

### 5.2 Чек-лист тестирования

✅ **Запуск и приветствие**
- [ ] Бот отвечает на /start
- [ ] Показывает главное меню

✅ **Статус парсера**
- [ ] Показывает текущий статус
- [ ] Отображает количество объектов
- [ ] Кнопка запуска видна когда парсер не работает

✅ **Журнал объектов**
- [ ] Пагинация работает (редактирует сообщение)
- [ ] Детали открываются новым сообщением
- [ ] "Назад к списку" удаляет карточку и возвращает журнал

✅ **Запуск парсера**
- [ ] Бот не зависает при запуске
- [ ] Показывает промежуточные статусы
- [ ] Выводит итоговый отчет
- [ ] При ошибке 429 показывает понятное сообщение

✅ **Docker**
- [ ] Контейнер запускается
- [ ] База данных сохраняется
- [ ] Бот перезапускается при падении

---

## ШАГ 6: Решение типичных проблем

### Проблема: "Предыдущее сообщение потеряно"
**Решение:** Карточка объекта отправляется новым сообщением, при возврате удаляется

### Проблема: Бот зависает при парсинге
**Решение:** Парсер запускается в отдельном потоке через `threading.Thread`

### Проблема: Ошибка 429 от Avito
**Решение:** Показываем понятное сообщение пользователю с рекомендациями

### Проблема: Импорты не работают
**Решение:** Добавлен `sys.path.append` в начале файлов бота

---

## Финальная команда для Cursor

Если хотите сгенерировать всё одной командой:

> Создай модуль `telegram_bot/` с файлами из этой инструкции. Структура: `bot.py` (главный), `handlers.py` (обработчики), `keyboards.py` (клавиатуры), `parser_runner.py` (интеграция). В `database/database_manager.py` добавь методы `get_listings_count()`, `get_listings_page()`, `get_listing_by_id()`. Убедись что все импорты работают с текущей структурой проекта. Токен берется из TELEGRAM_BOT_TOKEN в .env. Запуск парсера в отдельном потоке с обратной связью. Журнал с пагинацией через редактирование, детали - новым сообщением.

---

**Готово!**