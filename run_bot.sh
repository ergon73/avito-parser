#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Activate venv if present
if [[ -d "venv" ]]; then
  # shellcheck disable=SC1091
  source venv/bin/activate || true
elif [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate || true
fi

# Ensure required deps (idempotent)
python -m pip install -q --disable-pip-version-check pyTelegramBotAPI APScheduler >/dev/null 2>&1 || true

exec python telegram_bot/bot.py


