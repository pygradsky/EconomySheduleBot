# 📅 Institute Schedule Telegram Mini App

Telegram Mini App для просмотра расписания института с парсингом PDF и кэшированием.

---

## 🏗️ Архитектура

```
schedule_bot/
├── backend/
│   ├── api/
│   │   ├── routes.py           # FastAPI эндпоинты
│   │   └── schedule_service.py # Сервис загрузки и кэша
│   ├── cache/
│   │   └── memory_cache.py     # In-memory кэш с TTL
│   ├── models/
│   │   └── schedule.py         # Pydantic модели данных
│   ├── parsers/
│   │   └── pdf_parser.py       # Парсер PDF (pdfplumber + PyMuPDF)
│   ├── config.py               # Настройки (pydantic-settings)
│   └── main.py                 # FastAPI приложение
├── frontend/
│   └── index.html              # Mini App (HTML/CSS/JS, без фреймворков)
├── data/
│   └── schedule/
│       ├── 1/economy_1.pdf
│       ├── 2/economy_2.pdf
│       ├── 3/economy_3.pdf
│       └── 4/economy_4.pdf
├── logs/
├── bot.py                      # Telegram Bot (python-telegram-bot)
├── run.py                      # Запуск API + бота
├── generate_demo_pdf.py        # Генератор тестовых PDF
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## ⚡ Быстрый старт

### 1. Клонируй / распакуй проект

```bash
cd schedule_bot
```

### 2. Создай виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows
```

### 3. Установи зависимости

```bash
pip install -r requirements.txt
# Для генерации тестовых PDF:
pip install reportlab
```

### 4. Настрой `.env`

```bash
cp .env.example .env
```

Отредактируй `.env`:
```
BOT_TOKEN=1234567890:AABBccDDeeFFggHH...   # токен от @BotFather
WEBAPP_URL=https://your-domain.com          # публичный URL Mini App
PORT=8000
```

> **WEBAPP_URL** должен быть публичным HTTPS-адресом (Telegram требует HTTPS для Mini Apps).
> Для локальной разработки используй [ngrok](https://ngrok.com/):
> ```bash
> ngrok http 8000
> # Скопируй https://xxxx.ngrok.io и вставь в WEBAPP_URL
> ```

### 5. Добавь PDF-файлы расписаний

Положи PDF файлы по путям:
```
data/schedule/1/economy_1.pdf
data/schedule/2/economy_2.pdf
data/schedule/3/economy_3.pdf
data/schedule/4/economy_4.pdf
```

**Или сгенерируй демо-данные:**
```bash
python generate_demo_pdf.py
```

### 6. Запуск

```bash
python run.py
```

Или раздельно:

```bash
# Только API
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Только бот (в другом терминале)
python bot.py
```

---

## 🐳 Docker

```bash
docker-compose up --build
```

---

## 📡 API

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/health` | Статус сервиса |
| GET | `/api/v1/courses` | Список курсов |
| GET | `/api/v1/courses/{course}/groups` | Группы курса |
| GET | `/api/v1/courses/{course}/groups/{group}/schedule` | Расписание группы |
| POST | `/api/v1/admin/reload/{course}` | Перезагрузить PDF |

**Параметры:**
- `?search=ЭК` — фильтрация групп по имени

**Пример ответа расписания:**
```json
{
  "group": "ЭК-11",
  "course": 1,
  "hash": "a1b2c3d4",
  "days": [
    {
      "day": "Понедельник",
      "day_en": "monday",
      "lessons": [
        {
          "time_start": "08:30",
          "time_end": "10:00",
          "subject": "Математический анализ",
          "teacher": "Иванов А.А.",
          "room": "101",
          "lesson_type": "lecture",
          "week_type": null,
          "subgroup": null
        }
      ]
    }
  ]
}
```

---

## 🎨 Типы занятий

| Тип | Ключевые слова в PDF | Цвет |
|-----|---------------------|------|
| `lecture` | лек, лекция | 🔵 Синий |
| `practice` | пр, практ | 🟢 Зелёный |
| `seminar` | сем, семинар | 🟡 Жёлтый |
| `lab` | лаб, лабор | 🟣 Фиолетовый |
| `exam` | экз, зачет | 🔴 Красный |
| `other` | всё остальное | ⚪ Серый |

---

## 🔧 Настройка парсера под свой PDF

Если парсер не распознаёт твои PDF — отредактируй в `backend/parsers/pdf_parser.py`:

1. **`GROUP_PATTERN`** — regex для распознавания групп (напр. `ЭК-11`)
2. **`TIME_PATTERN`** — regex для времени занятий
3. **`LESSON_TYPE_KEYWORDS`** — словарь ключевых слов для типов занятий
4. **`parse_table_to_schedule()`** — логика разбора таблицы

**Отладка парсера:**
```python
from backend.parsers.pdf_parser import parse_pdf
from pathlib import Path

result = parse_pdf(Path("data/schedule/1/economy_1.pdf"), course=1)
print(result.groups)
for group, schedule in result.schedules.items():
    print(f"\n{group}:")
    for day in schedule.days:
        print(f"  {day.day}: {len(day.lessons)} занятий")
```

---

## 📱 Mini App

Mini App открывается кнопкой в боте при команде `/start`.

**Функционал:**
- Выбор курса (1-4) — вкладки вверху
- Поиск группы в реальном времени
- Расписание по дням с навигацией
- Цветные бейджи типов занятий
- Автоматическое кэширование на клиенте
- Поддержка тёмной/светлой темы Telegram

---

## ⚠️ Troubleshooting

**PDF не парсится:**
- Убедись, что PDF содержит текстовый слой (не отсканированный образ)
- Для отсканированных PDF нужен OCR (Tesseract)
- Попробуй `pdfplumber` / `PyMuPDF` вручную

**Mini App не открывается:**
- WEBAPP_URL должен быть HTTPS
- Домен должен быть публичным (не localhost)
- Проверь сертификат SSL

**Бот не отвечает:**
- Проверь BOT_TOKEN в `.env`
- Убедись что бот не запущен в другом процессе
