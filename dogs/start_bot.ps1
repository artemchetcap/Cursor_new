# Start Bot Script
Write-Host "Starting bot setup..." -ForegroundColor Cyan

# Step 1: Copy env.example to .env if .env doesn't exist
if (-not (Test-Path ".\.env")) {
    Write-Host "Creating .env from env.example..." -ForegroundColor Yellow
    Copy-Item ".\env.example" ".\.env"
    Write-Host ".env created! Please edit it with your tokens:" -ForegroundColor Green
    Write-Host "  TG_TOKEN=<your Telegram bot token from @BotFather>" -ForegroundColor White
    Write-Host "  OPENAI_API_KEY=<your OpenAI API key>" -ForegroundColor White
    Write-Host "  ADMIN_IDS=<your Telegram ID>" -ForegroundColor White
    Write-Host ""
    Write-Host "After editing .env, run this script again to start the bot." -ForegroundColor Cyan
    exit 0
}

Write-Host ".env file exists. Starting bot..." -ForegroundColor Green

# Step 2: Run the bot
.\.venv\Scripts\python.exe main.py

