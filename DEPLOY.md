# Руководство по деплою (Ubuntu 24.04 + Docker)

Подробный гайд по развёртыванию проекта на VPS. Учтены рекомендации из `opus_deploy.txt` и `gemini_deploy.txt`.

## 1. Требования
- VPS x86_64 (рекомендовано ≥2 vCPU / 2 GB RAM)
- Ubuntu 22.04/24.04
- Доступ в интернет (Telegram Bot API)
- Токен бота `TELEGRAM_BOT_TOKEN`

## 2. Установка Docker и Compose
```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo apt-get install -y docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker

# Проверка
docker --version
docker compose version
```

## 3. Клонирование проекта
```bash
git clone <ВАШ_РЕПОЗИТОРИЙ> avito-parser
cd avito-parser
```

## 4. Настройка .env
Создайте `.env` (секреты не коммитим):
```bash
cp .env.example .env 2>/dev/null || true
nano .env
```
Рекомендуемые значения для VPS:
```env
TARGET_URL=https://www.avito.ru/...
PARSER_MODE=playwright
USE_ANTIBOT_TRICKS=false
LOG_LEVEL=INFO
USE_HEADLESS=true
BROWSER_CHANNEL=chromium

# Telegram Bot
TELEGRAM_BOT_TOKEN=ВАШ_ТОКЕН
TELEGRAM_ADMIN_ID=
```

## 5. Папки и права
```bash
mkdir -p database logs trash cookies
chmod 777 database logs trash cookies
```
Прод: можно ужесточить права (`chown -R appuser:appuser .`) и запускать контейнер под non-root.

## 6. Рекомендации по Docker Compose
Для стабильной работы браузера на Linux:
```yaml
services:
  avito-parser:
    shm_size: '512m'     # увеличить /dev/shm
    # ipc: host          # альтернатива (макс. совместимость)
  avito-parser-bot:
    environment:
      - PYTHONUNBUFFERED=1
      - TZ=Europe/Moscow
```
Если нужен только бот — достаточно сервиса `avito-parser-bot`.

## 7. Сборка и запуск
```bash
docker compose build
docker compose up -d
```
Применить изменения из `.env` без пересборки:
```bash
docker compose up -d --force-recreate
```

## 8. Проверка логов и статуса
```bash
docker compose logs -f --tail=100
docker compose ps
```

## 9. Частые проблемы
- "Cannot open display": используйте только headless (`USE_HEADLESS=true`), headed требует X-сервера (`xvfb-run`).
- Chromium не найден: в Dockerfile должна быть команда `playwright install chromium --with-deps`.
- Мало `/dev/shm`: добавьте `shm_size: '512m'`.
- Permission denied при записи БД/логов: `chmod 777 database logs` (или настройте владельца).
- ARM/aarch64: используйте x86_64 VPS или собирайте multi-arch образы.

## 10. Управление
```bash
# Перезапуск бота
docker compose restart avito-parser-bot
# Остановка
docker compose down
# Обновление кода
git pull && docker compose build --no-cache && docker compose up -d
```

## 11. Безопасность и эксплуатация
- `.env` хранить вне Git
- Секреты — в менеджере секретов/CI
- Ротация логов на уровне хоста
- Опционально: healthcheck и уведомления в бот при сбоях

---
Готово к продакшен-развёртыванию на Ubuntu 24.04.
