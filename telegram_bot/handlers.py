"""
Обработчики команд и колбэков
"""
from loguru import logger
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.database_manager import DatabaseManager
from .keyboards import main_menu, journal_navigation, listing_details, settings_menu
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
            if data == "menu":
                bot.edit_message_text(
                    "📋 <b>Главное меню</b>\n\nВыберите действие:",
                    chat_id, message_id,
                    reply_markup=main_menu(),
                    parse_mode='HTML'
                )

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

            elif data.startswith("journal:"):
                page = int(data.split(":")[1])
                show_journal(bot, chat_id, message_id, page)

            elif data.startswith("view:"):
                parts = data.split(":")
                listing_id = int(parts[1])
                page = int(parts[2])
                show_listing_details(bot, chat_id, listing_id, page)

            elif data.startswith("back_journal:"):
                page = int(data.split(":")[1])
                bot.delete_message(chat_id, message_id)
                msg = bot.send_message(chat_id, "Загружаю журнал...")
                show_journal(bot, chat_id, msg.message_id, page)

            elif data == "run_parser":
                if parser_runner.is_running:
                    bot.answer_callback_query(call.id, "⚠️ Парсер уже работает!", show_alert=True)
                else:
                    bot.answer_callback_query(call.id, "🚀 Запускаю парсер...")

                    def callback(status, message):
                        if status == "started":
                            bot.edit_message_text(message, chat_id, message_id, parse_mode='HTML')
                        else:
                            try:
                                bot.delete_message(chat_id, message_id)
                            except Exception:
                                pass
                            bot.send_message(chat_id, message, parse_mode='HTML')

                    result = parser_runner.run_parser(callback)
                    if not result['success']:
                        bot.answer_callback_query(call.id, result['error'], show_alert=True)

            elif data == "settings":
                bot.edit_message_text(
                    "⚙️ <b>Настройки</b>",
                    chat_id, message_id,
                    reply_markup=settings_menu(),
                    parse_mode='HTML'
                )

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


def show_journal(bot, chat_id, message_id, page: int = 1):
    """Отображает журнал объектов"""
    db = DatabaseManager()
    total = db.get_listings_count() if hasattr(db, 'get_listings_count') else 0

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

    listings = db.get_listings_page(page, ITEMS_PER_PAGE) if hasattr(db, 'get_listings_page') else []
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE if total else 1

    text = f"📖 <b>Журнал объектов</b>\nСтраница {page}/{total_pages}\n\n"

    bot.edit_message_text(
        text + "Выберите объект для просмотра:",
        chat_id, message_id,
        reply_markup=journal_navigation(page, total_pages, listings),
        parse_mode='HTML'
    )


def show_listing_details(bot, chat_id, listing_id: int, page: int):
    """Показывает детали объекта в новом сообщении"""
    db = DatabaseManager()
    listing = db.get_listing_by_id(listing_id) if hasattr(db, 'get_listing_by_id') else None

    if not listing:
        bot.answer_callback_query(chat_id, "Объект не найден", show_alert=True)
        return

    text = f"🏠 <b>{listing['title']}</b>\n\n"
    if listing.get('price'):
        text += f"💰 Цена: <b>{listing['price']}</b>\n"
    if listing.get('address'):
        text += f"📍 Адрес: {listing['address']}\n"
    if listing.get('description'):
        desc = listing['description'][:500]
        if len(listing['description']) > 500:
            desc += "..."
        text += f"\n📝 Описание:\n{desc}\n"

    bot.send_message(
        chat_id,
        text,
        reply_markup=listing_details(listing_id, page, listing['url']),
        parse_mode='HTML',
        disable_web_page_preview=True
    )


