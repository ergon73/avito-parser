# PowerShell launcher for Telegram bot (inside avito-parser)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location -Path $PSScriptRoot

# Activate venv if present
if (Test-Path -Path "venv/Scripts/Activate.ps1") {
    . "venv/Scripts/Activate.ps1"
} elseif (Test-Path -Path ".venv/Scripts/Activate.ps1") {
    . ".venv/Scripts/Activate.ps1"
}

# Ensure required deps
python -m pip install -q --disable-pip-version-check pyTelegramBotAPI APScheduler | Out-Null

# UTF-8 console
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
try { chcp 65001 > $null } catch { }

# Run bot
python telegram_bot/bot.py


