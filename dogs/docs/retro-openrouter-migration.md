# Ретроспектива: Миграция на OpenRouter

**Дата:** 2024-12-04  
**Проект:** GistBot (Telegram AI Bot)  
**Проблема:** Прямой Anthropic API блокируется (403 Forbidden)

---

## 🎯 Контекст проблемы

### Симптомы
```
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 403 Forbidden"
anthropic.PermissionDeniedError: Error code: 403 - {'error': {'type': 'forbidden', 'message': 'Request not allowed'}}
```

### Причина
Корпоративный файрвол/прокси блокирует прямые запросы к Anthropic API.

### Ограничения среды
- Корпоративная сеть с SSL-перехватом (self-signed certificate)
- Невозможность изменить сетевые настройки

---

## 💡 Решение: OpenRouter

**OpenRouter** — агрегатор LLM с OpenAI-совместимым API. Поддерживает Anthropic, OpenAI, Llama и другие модели через единый endpoint.

### Почему OpenRouter?
- ✅ OpenAI-совместимый API (можно использовать OpenAI SDK)
- ✅ Не блокируется корпоративными прокси
- ✅ Поддержка Claude моделей
- ✅ Pay-as-you-go без минимального депозита

---

## 🔧 Техническая реализация

### 1. Изменение клиента (client.py)

**Было:**
```python
from anthropic import AsyncAnthropic

self._client = AsyncAnthropic(
    api_key=api_key,
    http_client=_create_insecure_http_client(),
)

# Вызов нативного Anthropic API
response = await self._client.messages.create(
    system=system_prompt,
    model=self.model,
    messages=messages,
    ...
)
```

**Стало:**
```python
from openai import AsyncOpenAI, DefaultAsyncHttpxClient

def _create_insecure_http_client() -> DefaultAsyncHttpxClient:
    """HTTP client без проверки SSL для корпоративного прокси."""
    return DefaultAsyncHttpxClient(
        verify=False,
        timeout=httpx.Timeout(60.0, connect=30.0),
    )

self._client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,  # https://openrouter.ai/api/v1
    default_headers={
        "Authorization": f"Bearer {api_key}",  # ВАЖНО: явно!
        "HTTP-Referer": "https://t.me/YourBot",
        "X-Title": "YourBotName",
    },
    http_client=_create_insecure_http_client(),
)

# Вызов OpenAI-совместимого API
response = await self._client.chat.completions.create(
    model=self.model,
    messages=messages,  # Стандартный формат [{role, content}]
    ...
)
```

### 2. Конфигурация (config.py)

```python
class Settings(BaseSettings):
    # ... existing fields ...
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    ANTHROPIC_MODEL: str = "anthropic/claude-3.5-haiku"
    ANTHROPIC_BASE_URL: str = "https://openrouter.ai/api/v1"
```

### 3. Переменные окружения (.env)

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-or-v1-your-openrouter-key
ANTHROPIC_BASE_URL=https://openrouter.ai/api/v1
ANTHROPIC_MODEL=anthropic/claude-3.5-haiku
```

---

## ⚠️ Подводные камни и решения

### Проблема 1: SSL CERTIFICATE_VERIFY_FAILED
```
ssl.SSLCertificateVerifyError: certificate verify failed: self-signed certificate
```

**Причина:** Корпоративный прокси перехватывает HTTPS.

**Решение:**
```python
from openai import DefaultAsyncHttpxClient

http_client = DefaultAsyncHttpxClient(verify=False, ...)
```

> ⚠️ `verify=False` — только для корпоративных сетей. В продакшене используйте proper certificate handling.

---

### Проблема 2: 401 "No cookie auth credentials found"
```
{'error': {'message': 'No cookie auth credentials found', 'code': 401}}
```

**Причина:** При использовании кастомного `http_client` заголовок `Authorization` не передаётся автоматически.

**Решение:** Явно добавить в `default_headers`:
```python
default_headers={
    "Authorization": f"Bearer {api_key}",  # ← КРИТИЧЕСКИ ВАЖНО
    "HTTP-Referer": "https://your-app.com",
    "X-Title": "YourApp",
}
```

---

### Проблема 3: Дублирование переменных в .env
```
ANTHROPIC_API_KEY=sk-or-v1-correct-key
# ... много строк ...
ANTHROPIC_API_KEY=old-placeholder  # ← Перезаписывает первое!
```

**Причина:** `dotenv` читает файл сверху вниз, последнее значение побеждает.

**Решение:** Убедиться что каждая переменная указана только один раз.

---

### Проблема 4: 429 Rate Limit
```
{'message': 'anthropic/claude-3.5-haiku is temporarily rate-limited upstream'}
```

**Причина:** Бесплатные лимиты OpenRouter исчерпаны или модель перегружена.

**Решения:**
1. Подождать 5-10 минут
2. Пополнить баланс OpenRouter (увеличивает лимиты)
3. Использовать другую модель (например, `anthropic/claude-3.5-haiku` без `:free`)

---

### Проблема 5: Invalid model ID
```
{'message': 'anthropic/claude-3-haiku-20240307 is not a valid model ID'}
```

**Причина:** Неправильный формат ID модели для OpenRouter.

**Решение:** Использовать формат `provider/model-name`:
- ✅ `anthropic/claude-3.5-haiku`
- ✅ `anthropic/claude-3.5-sonnet`
- ❌ `anthropic/claude-3-haiku-20240307`
- ❌ `claude-3.5-haiku` (без провайдера)

Список моделей: https://openrouter.ai/models

---

## 📋 Чеклист для будущих проектов

### Начальная настройка OpenRouter
- [ ] Зарегистрироваться на https://openrouter.ai
- [ ] Создать API ключ (Keys → Create Key)
- [ ] Опционально: пополнить баланс для увеличения лимитов

### Код
- [ ] Использовать `AsyncOpenAI` / `OpenAI` из `openai` пакета
- [ ] Указать `base_url="https://openrouter.ai/api/v1"`
- [ ] Добавить `Authorization` header явно в `default_headers`
- [ ] Использовать `DefaultAsyncHttpxClient(verify=False)` для корпоративных сетей
- [ ] Добавить `HTTP-Referer` и `X-Title` headers (рекомендуется OpenRouter)

### Конфигурация
- [ ] Добавить `*_BASE_URL` настройку для гибкости
- [ ] Использовать формат модели `provider/model-name`
- [ ] Проверить `.env` на дубликаты переменных

---

## 🔗 Полезные ссылки

- **OpenRouter:** https://openrouter.ai
- **OpenRouter Docs:** https://openrouter.ai/docs
- **Модели:** https://openrouter.ai/models
- **API Keys:** https://openrouter.ai/keys
- **OpenAI Python SDK:** https://github.com/openai/openai-python

---

## 📝 Пример минимальной интеграции

```python
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
import os

client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "HTTP-Referer": "https://your-app.com",
        "X-Title": "YourApp",
    },
    # Для корпоративных сетей с SSL-перехватом:
    http_client=DefaultAsyncHttpxClient(verify=False),
)

response = await client.chat.completions.create(
    model="anthropic/claude-3.5-haiku",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
    max_tokens=100,
)

print(response.choices[0].message.content)
```

---

## ✅ Результат

Бот успешно работает через OpenRouter, обходя корпоративные ограничения на прямой доступ к Anthropic API.

