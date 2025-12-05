# 🧠 Smart Summarizer Bot

> AI-powered Telegram bot that extracts key insights from YouTube videos, web articles, and text.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp env.example .env
# Edit .env with your tokens
```

3. **Run migrations:**
```bash
aerich upgrade
```

4. **Start the bot:**
```bash
python main.py
```

## Features

- 🎬 **YouTube** — extract subtitles and summarize videos
- 📰 **Web Articles** — parse and summarize any article
- 📝 **Text** — direct text summarization
- 📊 **Admin Stats** — usage analytics for admins

## Documentation

- [Product Spec](docs/Product.md) — product vision and user flows
- [Tech Spec](docs/Tech.md) — architecture and technical details
- [Deploy Guide](docs/deploy-timeweb.md) — деплой на Timeweb Cloud (149₽/мес)

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Usage instructions |
| `/stats` | Admin statistics (restricted) |

