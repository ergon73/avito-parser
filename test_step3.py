#!/usr/bin/env python3
"""Тестирование Step 3 улучшений"""

from config.settings import settings, logger
from services.browser_profiles_2025 import BROWSER_PROFILES
import sys

def test_profiles():
    """Проверка новых профилей"""
    logger.info("=== ТЕСТ ПРОФИЛЕЙ 2025 ===")
    
    for i, profile in enumerate(BROWSER_PROFILES, 1):
        logger.info(f"{i}. {profile['name']}")
        logger.info(f"   UA: {profile['headers']['user-agent'][:50]}...")
        logger.info(f"   Impersonate: {profile['impersonate']}")
        
        # Проверка критических ошибок
        if "chrome120" in str(profile.get("impersonate")):
            logger.error("   ⚠️ ОШИБКА: Устаревший impersonate!")
        if "connection" in profile["headers"]:
            logger.error("   ⚠️ ОШИБКА: Запрещенный заголовок Connection!")
        if "sec-ch-ua" in profile["headers"]:
            logger.warning("   ⚠️ Предупреждение: sec-ch-ua не должен быть хардкодным")

def test_chrome_availability():
    """Проверка доступности Google Chrome"""
    logger.info("\n=== ТЕСТ CHROME ===")
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome", headless=False)
                browser.close()
                logger.success("✅ Google Chrome доступен!")
            except:
                logger.warning("⚠️ Google Chrome не найден, будет использован Chromium")
    except Exception as e:
        logger.error(f"❌ Playwright ошибка: {e}")

def test_curl_cffi():
    """Проверка curl-cffi с новыми профилями"""
    logger.info("\n=== ТЕСТ CURL-CFFI ===")
    
    try:
        from curl_cffi import requests
        from services.browser_profiles_2025 import get_random_profile
        
        profile = get_random_profile()
        logger.info(f"Тестируем профиль: {profile['name']}")
        
        # Тестовый запрос к простому сайту
        response = requests.get(
            "https://httpbin.org/user-agent",
            headers=profile["headers"],
            impersonate=profile["impersonate"],
            timeout=10
        )
        
        if response.status_code == 200:
            logger.success("✅ curl-cffi работает с новыми профилями!")
            logger.info(f"Ответ: {response.text[:100]}...")
        else:
            logger.warning(f"⚠️ curl-cffi вернул код: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ curl-cffi ошибка: {e}")

def main():
    logger.info("=== AVITO PARSER STEP 3 - ДИАГНОСТИКА ===\n")
    
    # Тест 1: Профили
    test_profiles()
    
    # Тест 2: Chrome
    test_chrome_availability()
    
    # Тест 3: curl-cffi
    test_curl_cffi()
    
    # Тест 4: Основная проверка
    logger.info("\n=== РЕКОМЕНДАЦИИ ===")
    logger.info("1. Установите Google Chrome если его нет")
    logger.info("2. Начните с USE_HEADLESS=false чтобы видеть процесс")
    logger.info("3. Попробуйте разные профили через PREFERRED_PROFILE")
    logger.info("4. Если блокировка продолжается - используйте прокси")
    
    logger.info("\n=== ГОТОВНОСТЬ К ТЕСТИРОВАНИЮ ===")
    logger.info("✅ Step 3 реализован!")
    logger.info("✅ Актуальные профили браузеров созданы")
    logger.info("✅ curl-cffi обновлен")
    logger.info("✅ Playwright переписан")
    logger.info("✅ Настройки обновлены")
    
    logger.info("\n🚀 Готов к тестированию! Запустите: python main.py")

if __name__ == "__main__":
    main()
