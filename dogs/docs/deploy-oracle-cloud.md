# Деплой на Oracle Cloud Free Tier (без Docker)

> Пошаговая инструкция по запуску бота на бесплатном сервере Oracle Cloud.

---

## Шаг 1: Регистрация в Oracle Cloud

1. Перейди на https://www.oracle.com/cloud/free/
2. Нажми **"Start for free"**
3. Заполни форму:
   - Email (рабочий, не временный)
   - Страна: любая (рекомендую Germany/Netherlands для низкого пинга)
   - **Нужна банковская карта** — спишут $1 для верификации и вернут
4. Подтверди email и дождись активации (до 24ч, обычно быстрее)

⚠️ **Важно:** Используй реальные данные — Oracle проверяет и банит фейки.

---

## Шаг 2: Создание сервера (VM Instance)

1. Зайди в консоль: https://cloud.oracle.com/
2. **Меню → Compute → Instances → Create Instance**

3. Настройки:
   | Параметр | Значение |
   |----------|----------|
   | Name | `summarizer-bot` |
   | Image | **Ubuntu 22.04** (или Canonical Ubuntu) |
   | Shape | **VM.Standard.E2.1.Micro** (Always Free) |
   | OCPU | 1 |
   | Memory | 1 GB |

4. **Networking:**
   - Выбери существующий VCN или создай новый
   - Отметь **"Assign a public IPv4 address"** ✅

5. **SSH Keys:**
   - Выбери **"Generate a key pair for me"**
   - **Скачай оба ключа** (private и public) — без них не войдёшь!
   - Сохрани в надёжное место

6. Нажми **"Create"** и дождись статуса **RUNNING** (2-3 минуты)

7. **Запиши Public IP** — он понадобится для подключения

---

## Шаг 3: Открытие портов (Security List)

По умолчанию Oracle блокирует исходящие соединения. Нужно открыть:

1. **Меню → Networking → Virtual Cloud Networks**
2. Выбери свой VCN → **Security Lists** → Default Security List
3. **Add Egress Rules:**
   
   | Destination | Protocol | Ports | Description |
   |-------------|----------|-------|-------------|
   | 0.0.0.0/0 | TCP | All | Allow outbound |

4. Сохрани

---

## Шаг 4: Подключение к серверу

### Windows (PowerShell):
```powershell
# Путь к скачанному ключу
ssh -i C:\Users\ВашеИмя\Downloads\ssh-key-2024-xx-xx.key ubuntu@ВАШ_PUBLIC_IP
```

### Если ошибка с правами ключа (Windows):
```powershell
# Правой кнопкой на файл ключа → Свойства → Безопасность → Дополнительно
# Отключить наследование → Удалить все разрешения → Добавить только своего пользователя
```

### Или используй PuTTY:
1. Скачай PuTTY: https://www.putty.org/
2. Конвертируй ключ через PuTTYgen (Load → Save private key как .ppk)
3. В PuTTY: Host = Public IP, Connection → SSH → Auth → Private key = твой .ppk

---

## Шаг 5: Настройка сервера

После подключения выполни команды:

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Python и pip
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Проверить версию
python3.11 --version
```

---

## Шаг 6: Загрузка проекта

### Вариант A: Через Git (если есть репозиторий)
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git bot
cd bot
```

### Вариант B: Через SCP (загрузить файлы напрямую)

На **локальном компьютере** (PowerShell):
```powershell
# Создать архив (в папке dogs)
Compress-Archive -Path * -DestinationPath bot.zip

# Загрузить на сервер
scp -i C:\путь\к\ключу.key bot.zip ubuntu@ВАШ_IP:~/
```

На **сервере**:
```bash
cd ~
sudo apt install -y unzip
unzip bot.zip -d bot
cd bot
```

---

## Шаг 7: Настройка окружения

```bash
cd ~/bot

# Создать виртуальное окружение
python3.11 -m venv venv

# Активировать
source venv/bin/activate

# Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Шаг 8: Создание .env файла

```bash
nano .env
```

Вставь содержимое (замени на свои значения):
```
TG_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_OUTPUT_TOKENS=700
```

Сохрани: `Ctrl+O`, Enter, `Ctrl+X`

---

## Шаг 9: Запуск миграций

```bash
source venv/bin/activate
aerich upgrade
```

---

## Шаг 10: Тестовый запуск

```bash
python main.py
```

Если видишь `Bot started` — всё работает! Останови: `Ctrl+C`

---

## Шаг 11: Автозапуск через systemd

Создать сервис, чтобы бот работал 24/7 и перезапускался при падении:

```bash
sudo nano /etc/systemd/system/summarizer-bot.service
```

Вставь:
```ini
[Unit]
Description=Smart Summarizer Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bot
Environment=PATH=/home/ubuntu/bot/venv/bin
ExecStart=/home/ubuntu/bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Сохрани и выполни:
```bash
# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable summarizer-bot

# Запустить сервис
sudo systemctl start summarizer-bot

# Проверить статус
sudo systemctl status summarizer-bot
```

---

## Полезные команды

| Команда | Описание |
|---------|----------|
| `sudo systemctl status summarizer-bot` | Статус бота |
| `sudo systemctl restart summarizer-bot` | Перезапустить |
| `sudo systemctl stop summarizer-bot` | Остановить |
| `sudo journalctl -u summarizer-bot -f` | Логи в реальном времени |
| `sudo journalctl -u summarizer-bot -n 100` | Последние 100 строк логов |

---

## Обновление бота

```bash
cd ~/bot

# Остановить
sudo systemctl stop summarizer-bot

# Обновить код (если через git)
git pull

# Или перезалить файлы через SCP

# Обновить зависимости (если изменились)
source venv/bin/activate
pip install -r requirements.txt

# Миграции (если есть новые)
aerich upgrade

# Запустить
sudo systemctl start summarizer-bot
```

---

## Troubleshooting

### Ошибка "Connection refused"
- Проверь Security List (Шаг 3)
- Проверь, что используешь правильный IP

### Ошибка "Permission denied (publickey)"
- Проверь путь к ключу
- На Windows: исправь права доступа к файлу ключа

### Бот падает
```bash
# Смотри логи
sudo journalctl -u summarizer-bot -n 50

# Частая причина: неверный токен в .env
```

### Мало памяти
```bash
# Создать swap файл (добавит 1GB виртуальной памяти)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Сделать постоянным
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Готово! 🎉

Твой бот теперь работает 24/7 на бесплатном сервере Oracle Cloud.

**Стоимость:** $0/мес (навсегда, пока не превысишь лимиты Free Tier)

