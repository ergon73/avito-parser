#!/usr/bin/env python3
"""
Главный файл Telegram-бота
"""
import os
import sys
from pathlib import Path
from loguru import logger
import telebot

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
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("telegram_bot_token")

    if not token:
        logger.error("❌ Не найден TELEGRAM_BOT_TOKEN в .env файле!")
        logger.info("Добавьте в .env: TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather")
        sys.exit(1)

    bot = telebot.TeleBot(token, parse_mode='HTML')

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


