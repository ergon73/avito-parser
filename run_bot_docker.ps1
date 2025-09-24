# PowerShell helper to run Telegram bot in Docker
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location -Path $PSScriptRoot

# Build (optional incremental)
if ($args -contains '--build') {
  docker compose build
}

# Up only bot service
docker compose up -d --build avito-parser-bot

# Tail logs if requested
if ($args -contains '--logs') {
  docker compose logs -f --tail=100 avito-parser-bot
}


