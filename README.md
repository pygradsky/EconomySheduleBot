# 📅 Расписание занятий обучающихся — Telegram Mini App

Telegram Mini App для просмотра расписания института с парсингом PDF и кэшированием.

---

## 🏗️ Архитектура

```
schedule_bot/
├── backend/
│   ├── api/
│   │   ├── routes.py            # FastAPI эндпоинты
│   │   ├── schedule_service.py  # Сервис загрузки и кэша
│   │   └── week_utils.py        # Определение верхней/нижней недели
│   ├── cache/
│   │   └── memory_cache.py      # In-memory кэш с TTL и SHA-256
│   ├── models/
│   │   └── schedule.py          # Pydantic модели данных
│   ├── parsers/
│   │   └── pdf_parser.py        # Парсер PDF (pdfplumber)
│   ├── config.py                # Настройки через .env
│   └── main.py                  # FastAPI приложение
├── frontend/
│   └── index.html               # Mini App (HTML/CSS/JS, без фреймворков)
├── data/
│   └── schedule/
│       ├── 1/<любой_файл>.pdf
│       ├── 2/<любой_файл>.pdf
│       ├── 3/<любой_файл>.pdf
│       └── 4/<любой_файл>.pdf
├── logs/
├── bot.py                       # Telegram бот
├── run.py                       # Запуск API + бота
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## ⚡ Быстрый старт (локально)

### 1. Создай виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows
```

### 2. Установи зависимости

```bash
pip install -r requirements.txt
```

### 3. Настрой `.env`

```bash
cp .env.example .env
```

```
BOT_TOKEN=1234567890:AABBccDDeeFFggHH
WEBAPP_URL=https://твой-домен.com
HOST=0.0.0.0
PORT=8000
DATA_DIR=./data/schedule
```

### 4. Добавь PDF файлы расписаний

Положи любой PDF в соответствующую папку курса — название файла не важно:

```
data/schedule/1/расписание_1курс.pdf
data/schedule/2/расписание_2курс.pdf
data/schedule/3/расписание_3курс.pdf
data/schedule/4/расписание_4курс.pdf
```

### 5. Запуск

```bash
python run.py
```

Открой в браузере: `http://localhost:8000`

---

## 🚀 Деплой на Railway

1. Залей проект (с PDF файлами) на GitHub
2. Зайди на [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. В разделе **Variables** добавь:
   ```
   BOT_TOKEN=...
   WEBAPP_URL=https://твой-проект.up.railway.app
   HOST=0.0.0.0
   PORT=8000
   DATA_DIR=./data/schedule
   ```
4. В разделе **Settings → Networking** сгенерируй домен
5. У [@BotFather](https://t.me/BotFather): `/mybots → Bot Settings → Menu Button → Edit Menu Button URL` — вставь Railway URL

---

## 📡 API

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/v1/health` | Статус сервиса |
| GET | `/api/v1/week` | Текущая неделя (верхняя/нижняя) |
| GET | `/api/v1/courses` | Список курсов |
| GET | `/api/v1/courses/{course}/groups` | Группы курса |
| GET | `/api/v1/courses/{course}/groups/{group}/schedule` | Расписание группы |
| POST | `/api/v1/admin/reload/{course}` | Перезагрузить PDF курса |

**Пример ответа `/week`:**
```json
{
  "date": "2026-03-23",
  "week_start": "2026-03-23",
  "week_end": "2026-03-29",
  "is_even": true,
  "week_type": "even",
  "label": "Нижняя",
  "label_full": "Нижняя неделя"
}
```

**Пример ответа расписания:**
```json
{
  "group": "ДЭ 15-25",
  "course": 1,
  "days": [
    {
      "day": "Понедельник",
      "day_en": "monday",
      "lessons": [
        {
          "time_start": "09:00",
          "time_end": "10:35",
          "subject": "Математический анализ",
          "teacher": "КИЙКО П.В",
          "room": "12-Планетарий1",
          "lesson_type": "lecture",
          "week_type": "odd"
        }
      ]
    }
  ]
}
```

---

## 🎨 Типы занятий и цвета

| Тип | Ключевые слова в PDF | Цвет |
|-----|---------------------|------|
| `lecture` | лек. | 🟢 Зелёный |
| `practice` | пр. | 🟠 Оранжевый |
| `seminar` | сем. | 🟡 Жёлтый |
| `lab` | лаб. | 🟣 Фиолетовый |
| `exam` | экз. | 🔴 Красный |
| `other` | всё остальное | ⚪ Серый |

---

## 📅 Логика недель

Якорь: **23 марта 2026 (пн) = Нижняя неделя (чётная)**.

Недели чередуются математически от якоря — работает корректно после любого перезапуска. Чтобы сменить якорь, отредактируй `backend/api/week_utils.py`:

```python
ANCHOR_MONDAY = (2026, 3, 23)
ANCHOR_IS_EVEN = True
```

---

## 🔧 Формат PDF

Парсер ожидает таблицу вида:

| Дни | Часы | Группа 1 | Группа 2 | ... |
|-----|------|----------|----------|-----|
| ПОНЕДЕЛЬНИК | 09.00-10.35 | лек.Предмет ПРЕПОД ауд. | | |
| | | лек.Предмет ПРЕПОД ауд. | | |

- Строка **с временем** → верхняя неделя (`odd`)
- Строка **без времени** сразу после → нижняя неделя (`even`)
- Слот только с одним занятием → обе недели (`null`)

---

## ⚠️ Troubleshooting

**PDF не парсится (0 групп):**
- PDF должен содержать текстовый слой (не скан)
- Проверь логи при старте — там написано сколько групп загружено
- Если 0 групп — бот покажет демо-данные

**Mini App не открывается:**
- `WEBAPP_URL` должен быть HTTPS
- Проверь что домен публичный

**Бот не отвечает:**
- Проверь `BOT_TOKEN` в Variables на Railway
- Логи: Railway → Deployments → View Logs
