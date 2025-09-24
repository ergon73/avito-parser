#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ "${1:-}" == "--build" ]]; then
  docker compose build
fi

docker compose up -d --build avito-parser-bot

if [[ "${1:-}" == "--logs" || "${2:-}" == "--logs" ]]; then
  docker compose logs -f --tail=100 avito-parser-bot
fi


