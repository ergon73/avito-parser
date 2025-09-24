#!/usr/bin/env python3
"""
Скрипт для запуска парсера с настройками Playwright
"""
import os
import sys

# Устанавливаем переменные окружения перед импортом настроек
os.environ["PARSER_MODE"] = "playwright"
os.environ["USE_ANTIBOT_TRICKS"] = "false"

# Теперь импортируем и запускаем main
from main import main

if __name__ == "__main__":
    main()
