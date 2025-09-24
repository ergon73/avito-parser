"""
Актуальные профили браузеров на сентябрь 2025
КРИТИЧНО: Минимум заголовков, доверяем автогенерации
"""
import random

BROWSER_PROFILES = [
    # Chrome 140 на Windows - АКТУАЛЬНО на сентябрь 2025
    {
        "name": "Chrome Windows",
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        },
        "impersonate": "chrome",  # НЕ chrome120! Автовыбор последней версии
        "viewport": {"width": 1920, "height": 1080},
        "platform": "windows"
    },
    # Chrome на macOS
    {
        "name": "Chrome macOS", 
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        },
        "impersonate": "chrome",
        "viewport": {"width": 1440, "height": 900},
        "platform": "mac"
    },
    # Firefox 143 на Windows - АКТУАЛЬНО на сентябрь 2025
    {
        "name": "Firefox Windows",
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0",
            # НЕТ Connection: keep-alive! Запрещен в HTTP/2
        },
        "impersonate": "firefox",  # НЕ firefox110!
        "viewport": {"width": 1920, "height": 1080},
        "platform": "windows"
    },
    # Safari 18 на macOS
    {
        "name": "Safari macOS",
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "ru-RU",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        },
        "impersonate": "safari",
        "viewport": {"width": 1440, "height": 900},
        "platform": "mac"
    },
    # Edge 140 на Windows
    {
        "name": "Edge Windows",
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ru-RU,ru;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        },
        "impersonate": "edge",
        "viewport": {"width": 1920, "height": 1080},
        "platform": "windows"
    }
]

# КРИТИЧНО: НЕ добавляем эти заголовки - они автогенерируются:
# - sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform (GREASE-рандомизация) 
# - sec-fetch-dest, sec-fetch-mode, sec-fetch-site (контекстные)
# - connection, cache-control (управляются браузером)

def get_random_profile():
    """Возвращает случайный профиль"""
    return random.choice(BROWSER_PROFILES)

def get_profile_by_name(name):
    """Возвращает профиль по имени"""
    for profile in BROWSER_PROFILES:
        if profile["name"] == name:
            return profile
    return BROWSER_PROFILES[0]
