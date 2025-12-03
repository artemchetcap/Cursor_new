# 🏗 Architecture & Technology Stack (Tech Spec)

> **Статус документа**: DRAFT (v1.0)
> **Назначение**: Технический фундамент для разработки Smart Summarizer Bot.

---

## 1. High-Level Architecture (C4 Context)

Приложение построено как **модульный монолит** с асинхронной обработкой событий.

```mermaid
graph TD
    User[Telegram User] -->|Commands & Links| TG[Telegram API]
    TG -->|Webhooks/Polling| Bot[Smart Summarizer Bot]
    
    subgraph "Core System"
        Bot -->|Route| Handler[Message Handlers]
        Handler -->|Extract| Parser[Content Parser Service]
        Parser -->|Summarize| LLM[LLM Service (OpenAI/Claude)]
        Bot -->|Store User Data| DB[(Database / Redis)]
    end
    
    Parser -->|Get Video Subs| YT[YouTube API / yt-dlp]
    Parser -->|Get Article Text| Web[Web Scraper]
```

---

## 2. Technology Stack

### 🔹 Core
*   **Language**: Python 3.11+ (Строгая типизация `mypy`).
*   **Framework**: `aiogram 3.x` (Асинхронный, лучший для Telegram).
*   **Concurrency**: `asyncio` (Весь I/O неблокирующий).

### 🔹 Data Parsing (ETL)
*   **Video**: `yt-dlp` (Лучший инструмент для извлечения метаданных и субтитров YouTube).
*   **Web**: `newspaper3k` или `BeautifulSoup4` + `httpx` (Для парсинга статей).
*   **OCR/Vision**: `pytesseract` (локально) или Vision API LLM (для MVP - Vision API проще).

### 🔹 Intelligence (AI)
*   **LLM Orchestration**: Прямые вызовы API (без LangChain для простоты MVP, или `openai` SDK).
*   **Models**:
    *   Primary: `gpt-4o-mini` (Баланс цены/качества для саммари).
    *   Fallback: `claude-3-haiku` (Если нужны большие контекстные окна).

#### ⚙️ Настройки LLM (env)
*   `LLM_PROVIDER`: `openai` (по умолчанию) или `anthropic`.
*   `OPENAI_MODEL`, `OPENAI_MAX_OUTPUT_TOKENS`: управление таргет-моделью и длиной ответа.
*   `ANTHROPIC_MODEL`, `ANTHROPIC_MAX_OUTPUT_TOKENS`, `ANTHROPIC_API_KEY`: включаются при выборе провайдера `anthropic`.

### 🔹 Database & Storage
*   **Main DB**: `SQLite` (для MVP) -> `PostgreSQL` (Prod).
*   **Cache/State**: `Redis` (FSM состояния aiogram, кэширование ответов парсера).
*   **Vectors**: `ChromaDB` (задел на будущее для RAG, пока не внедряем в MVP).

### 🔹 Infrastructure
*   **Containerization**: Docker + Docker Compose.
*   **CI/CD**: GitHub Actions (Linting -> Build).
*   **Logging**: `structlog` (JSON логи для удобного поиска).

---

## 3. Data Flow (Pipeline)

Процесс обработки сообщения проходит через пайплайн:

1.  **Ingestion**: `Router` определяет тип контента (URL, Text, Photo).
2.  **Validation**: Проверка URL на валидность и доступность.
3.  **Extraction (Scraping)**:
    *   Если YouTube -> качаем `.vtt` (субтитры).
    *   Если Статья -> вычищаем HTML, оставляем `Title` + `Body`.
    *   Если Фото -> OCR/Vision -> Текст.
4.  **Transformation (LLM)**:
    *   Подготовка промпта с контекстом.
    *   Отправка в LLM с требованием JSON/Markdown структуры.
5.  **Presentation**: Формирование красивого ответа (карточка).

---

## 4. Project Structure (Monorepo)

```text
dogs/
├── app/
│   ├── bot/                # Telegram related logic
│   │   ├── handlers/       # Command & Message routers
│   │   ├── keyboards/      # Inline/Reply buttons
│   │   ├── middlewares/    # Logging, Throttling
│   │   └── states/         # FSM States
│   ├── core/               # Business Logic (Agnostic of Telegram)
│   │   ├── config.py       # Pydantic settings
│   │   ├── llm/            # LLM Client Wrappers
│   │   └── parsers/        # Scrapers (YouTube, Web, PDF)
│   ├── database/           # Models & Migrations
│   └── utils/              # Helper functions
├── docs/                   # Documentation (Tech.md, Product.md)
├── .env.example            # Environment template
├── Dockerfile
├── main.py                 # Entry point
└── requirements.txt        # Dependencies
```

---

## 5. Security & Limits

### Token Management
*   API ключи (`TG_TOKEN`, `OPENAI_API_KEY`) хранятся **ТОЛЬКО** в `.env`.
*   `.env` добавлен в `.gitignore`.

### Rate Limiting
*   Telegram: Стандартные лимиты (30 msg/sec).
*   LLM: Ограничение очереди запросов от одного юзера (чтобы не сжечь бюджет).

### Data Privacy
*   Мы не храним тексты пользователей долгосрочно в MVP (только логи обработки).
*   В будущем: Encryption at rest для базы знаний.

---

## 6. Telegram Bot Commands

### User Commands
| Command | Description |
|---------|-------------|
| `/start` | Приветственное сообщение с описанием бота |
| `/help` | Инструкция по использованию |

### Admin Commands
| Command | Access | Description |
|---------|--------|-------------|
| `/stats` | `ADMIN_IDS` | Статистика за 24ч и 7 дней (пользователи, запросы, токены) |

### Message Handlers
Бот обрабатывает следующие типы контента:
*   **YouTube ссылки** → извлечение субтитров + саммари
*   **Web статьи** → парсинг текста + саммари
*   **Текст** → прямое саммари
*   **Forwarded сообщения** → обработка как текст

### User Flow
1. Пользователь отправляет ссылку/текст
2. Бот ставит реакцию 👀 (acknowledgment)
3. Определяется тип контента, запускается парсинг
4. Контент отправляется в LLM для саммаризации
5. Результат отправляется пользователю с footer `⚡️ Fast read`
6. При успехе — реакция ✅

---

## 7. Running the Bot

### Environment Variables
```bash
# Telegram
TG_TOKEN=your_bot_token
ADMIN_IDS=123456789,987654321

# LLM Provider
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_OUTPUT_TOKENS=700

# Optional: Anthropic
ANTHROPIC_API_KEY=optional
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### Start Command
```bash
cd dogs
python main.py
```

---

## 8. Development Guidelines
*   **Code Style**: `PEP8` + `Black` formatter.
*   **Typing**: 100% покрытие тайп-хинтами.
*   **Commits**: Conventional Commits (`feat: add youtube parser`).

