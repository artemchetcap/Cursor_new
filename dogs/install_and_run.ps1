# Install missing dependencies and run bot
Set-Location $PSScriptRoot

Write-Host "Installing tiktoken..." -ForegroundColor Yellow
.\.venv\Scripts\pip.exe install tiktoken anthropic openai --quiet

Write-Host "Starting bot..." -ForegroundColor Green
.\.venv\Scripts\python.exe main.py

