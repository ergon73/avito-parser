"""
Клавиатуры для Telegram-бота
"""
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
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


def journal_navigation(current_page: int, total_pages: int, listings: list) -> InlineKeyboardMarkup:
    """Навигация по журналу с кнопками объектов"""
    markup = InlineKeyboardMarkup(row_width=1)

    for listing in listings:
        btn_text = f"🏠 {listing['title'][:40]}... - {listing['price']}"
        markup.add(InlineKeyboardButton(
            btn_text,
            callback_data=f"view:{listing['id']}:{current_page}"
        ))

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


def listing_details(listing_id: int, page: int, url: str) -> InlineKeyboardMarkup:
    """Кнопки для детальной карточки"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔗 Открыть на Avito", url=url),
        InlineKeyboardButton("🔙 Назад к списку", callback_data=f"back_journal:{page}")
    )
    return markup


def settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек"""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🔄 Автозапуск", callback_data="autorun_menu"),
        InlineKeyboardButton("📝 Изменить URL", callback_data="change_url"),
        InlineKeyboardButton("🔙 Назад", callback_data="menu")
    )
    return markup


