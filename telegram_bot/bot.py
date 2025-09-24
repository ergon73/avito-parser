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
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("telegram_bot_token")

    if not token:
        logger.error("❌ Не найден TELEGRAM_BOT_TOKEN в .env файле!")
        logger.info("Добавьте в .env: TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather")
        sys.exit(1)

    # Увеличиваем таймауты Telegram API (исправляет Read timed out / query is too old)
    apihelper.CONNECT_TIMEOUT = 30
    apihelper.READ_TIMEOUT = 60

    bot = telebot.TeleBot(token, parse_mode='HTML', threaded=True)

    register_handlers(bot)

    logger.success("✅ Avito Parser Bot запущен!")
    logger.info("Нажмите Ctrl+C для остановки")

    try:
        # Более устойчивый режим long polling
        bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


