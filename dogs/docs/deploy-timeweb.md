# Деплой на Timeweb Cloud (Россия)

> Пошаговая инструкция по запуску бота на российском хостинге Timeweb Cloud.

**Стоимость:** от 149₽/мес  
**Оплата:** Карты РФ, СБП, ЮMoney

---

## Шаг 1: Регистрация

1. Перейди на https://timeweb.cloud/
2. Нажми **"Регистрация"**
3. Введи email и пароль (или войди через VK/Яндекс)
4. Подтверди email
5. Пополни баланс (от 100₽) — карта РФ или СБП

---

## Шаг 2: Создание сервера

1. **Облачные серверы → Создать**

2. Настройки:
   | Параметр | Значение |
   |----------|----------|
   | ОС | **Ubuntu 22.04** |
   | Конфигурация | **Cloud 1** (1 vCPU, 1 GB RAM, 15 GB SSD) |
   | Датацентр | Москва или Санкт-Петербург |
   | Имя | `summarizer-bot` |

3. **SSH-ключ:**
   - Если есть — добавь публичный ключ
   - Если нет — пароль придёт на email

4. Нажми **"Создать сервер"**

5. Дождись статуса **"Активен"** (1-2 минуты)

6. **Запиши IP-адрес** из панели управления

---

## Шаг 3: Подключение к серверу

### Windows (PowerShell):
```powershell
ssh root@ВАШ_IP_АДРЕС
```

Введи пароль из email (или используй SSH-ключ).

### Или через PuTTY:
1. Host: твой IP
2. Port: 22
3. Login: root
4. Password: из email

---

## Шаг 4: Настройка сервера

```bash
# Обновить систему
apt update && apt upgrade -y

# Установить Python 3.11
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3-pip git

# Проверить
python3.11 --version
```

---

## Шаг 5: Создание пользователя (безопасность)

```bash
# Создать пользователя bot
adduser bot --disabled-password --gecos ""

# Дать права на sudo (опционально)
usermod -aG sudo bot

# Переключиться на пользователя
su - bot
```

---

## Шаг 6: Загрузка проекта

### Вариант A: Через Git
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git bot
cd bot
```

### Вариант B: Через SCP (с локального ПК)

**На локальном компьютере (PowerShell):**
```powershell
# В папке dogs создать архив
cd C:\Users\ВашеИмя\Desktop\Cursor_new\dogs
Compress-Archive -Path * -DestinationPath bot.zip

# Загрузить на сервер
scp bot.zip root@ВАШ_IP:/home/bot/
```

**На сервере:**
```bash
su - bot
cd ~
unzip bot.zip -d bot
cd bot
```

---

## Шаг 7: Настройка окружения

```bash
cd ~/bot

# Создать venv
python3.11 -m venv venv

# Активировать
source venv/bin/activate

# Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Шаг 8: Создание .env

```bash
nano .env
```

Вставь:
```
TG_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_OUTPUT_TOKENS=700
```

Сохрани: `Ctrl+O` → Enter → `Ctrl+X`

---

## Шаг 9: Миграции БД

```bash
source venv/bin/activate
aerich upgrade
```

---

## Шаг 10: Тестовый запуск

```bash
python main.py
```

Если видишь логи запуска — работает! Останови: `Ctrl+C`

---

## Шаг 11: Автозапуск (systemd)

**Выйди в root:**
```bash
exit  # если под пользователем bot
```

**Создай сервис:**
```bash
nano /etc/systemd/system/summarizer-bot.service
```

Вставь:
```ini
[Unit]
Description=Smart Summarizer Telegram Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/home/bot/bot
Environment=PATH=/home/bot/bot/venv/bin
ExecStart=/home/bot/bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Сохрани и активируй:
```bash
systemctl daemon-reload
systemctl enable summarizer-bot
systemctl start summarizer-bot
systemctl status summarizer-bot
```

---

## Полезные команды

```bash
# Статус
systemctl status summarizer-bot

# Логи (в реальном времени)
journalctl -u summarizer-bot -f

# Перезапуск
systemctl restart summarizer-bot

# Остановка
systemctl stop summarizer-bot
```

---

## Обновление бота

```bash
# Остановить
systemctl stop summarizer-bot

# Обновить код
su - bot
cd ~/bot
git pull  # если через git

# Или перезалить файлы через SCP

# Обновить зависимости
source venv/bin/activate
pip install -r requirements.txt
aerich upgrade

# Выйти и запустить
exit
systemctl start summarizer-bot
```

---

## Мониторинг в панели Timeweb

В личном кабинете доступно:
- 📊 Графики CPU/RAM/Disk
- 📈 Статистика трафика  
- 🔔 Алерты при проблемах
- 💾 Бэкапы (платно)

---

## Стоимость

| Конфигурация | CPU | RAM | SSD | Цена |
|--------------|-----|-----|-----|------|
| Cloud 1 | 1 vCPU | 1 GB | 15 GB | **149₽/мес** |
| Cloud 2 | 1 vCPU | 2 GB | 30 GB | 249₽/мес |
| Cloud 3 | 2 vCPU | 4 GB | 50 GB | 499₽/мес |

**Для бота хватит Cloud 1** (149₽/мес).

---

## Готово! 🎉

Бот работает 24/7 на российском сервере.

**Плюсы Timeweb:**
- ✅ Оплата картами РФ
- ✅ Поддержка на русском
- ✅ Датацентры в России (низкий пинг)
- ✅ Простая панель управления

