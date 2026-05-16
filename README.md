[![OpenYellow](https://img.shields.io/endpoint?url=https://openyellow.org/data/badges/7/1040948355.json)](https://openyellow.org/grid?data=top&repo=1040948355)
[![Quality Gate Status](https://sonar.openbsl.ru/api/project_badges/measure?project=onevents&metric=alert_status)](https://sonar.openbsl.ru/dashboard?id=onevents)
[![Telegram](https://img.shields.io/badge/telegram-%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB-blue.svg?label=telegram)](https://t.me/OnEvents)
[![LICENSE](https://img.shields.io/github/license/crimsongoldteam/md_design?label=%D0%BB%D0%B8%D1%86%D0%B5%D0%BD%D0%B7%D0%B8%D1%8F)](https://github.com/bestuzheff/OnEvents/blob/main/LICENSE)

# 🎉 OnEvents

Календарь событий и вебинаров по **1С**.

## Адрес проекта

👉 [https://onevents.ru](https://onevents.ru)

---

## Зачем это нужно?

Мы собрали все события, связанные с **1С**, в одном месте. Многие из нас ездят по городам — по работе или для отдыха. И здорово, когда рядом проходит мероприятие по 1С: можно заглянуть, познакомиться с коллегами и узнать что-то новое.

---

## 🏗 Архитектура проекта

Проект построен по модульному принципу — каждый модуль отвечает за свою задачу:

```
OnEvents/
├── create_web.py              # Главный скрипт сборки
├── requirements.txt           # Python зависимости
├── Dockerfile                 # Docker конфигурация
│
├── utils/                     # Универсальные утилиты
│   ├── text.py                # Работа с текстом (очистка, слаг, время)
│   └── dates.py               # Работа с датами (склонение, интервалы)
│
├── url_utils/                 # Утилиты для URL
│   └── __init__.py            # Сокращение ссылок, UTM-метки, карты
│
├── ics_calendars/             # Генерация ICS календарей
│   ├── __init__.py            # Создание VEVENT событий
│   └── generators.py          # Публичные календари, файлы для скачивания
│
├── html/                      # Генерация HTML
│   ├── __init__.py            # Карточки событий и вебинаров
│   └── calendars.py           # Блоки подписки на календари
│
├── rss/                       # RSS лента
│   └── __init__.py            # Генерация RSS 2.0
│
├── json_export/               # JSON экспорт
│   └── __init__.py            # Файлы для импорта
│
├── events/                    # YAML файлы событий (входные данные)
├── webinars/                  # YAML файлы вебинаров (входные данные)
├── img/                       # Изображения событий
├── icons/                     # Иконки сайта (favicon, манифест)
└── tests/                     # Тесты всех модулей
```

### Как это работает?

1. **Входные данные** — YAML файлы в папках `events/` и `webinars/`
2. **Сборка** — `create_web.py` читает все файлы, генерирует контент
3. **Выход** — готовая статика в папке `site/` (HTML, календари, RSS, JSON)

---

## ⚙️ Как собрать проект

### Способ 1: Docker (рекомендуется)

Самый простой способ — собрать контейнер и запустить:

```bash
# Собираем образ
docker build -t onevents .

# Запускаем контейнер
docker run --rm -p 8080:80 onevents
```

После этого сайт будет доступен по адресу: 👉 [http://localhost:8080](http://localhost:8080)

**Что происходит при сборке:**
- Python скрипт читает все YAML файлы событий
- Генерирует HTML страницу с карточками
- Создает ICS календари (отдельные файлы для каждого события + общие)
- Генерирует RSS ленту
- Экспортирует JSON файлы для импорта на другие сайты

### Способ 2: Python локально

Если нужен полный контроль или разработка:

```bash
# 1. Создаем виртуальное окружение
python -m venv .venv

# 2. Активируем окружение
#    Windows (PowerShell):
.venv\Scripts\activate.ps1
#    Linux/macOS:
source .venv/bin/activate

# 3. Устанавливаем зависимости
pip install -r requirements.txt

# 4. Запускаем сборку
python create_web.py
```

Результат появится в папке `site/`.

---

## 📁 Структура выходных данных

После сборки в папке `site/` создаются:

```
site/
├── index.html              # Главная страница сайта
├── calendar/               # ICS календари для скачивания
│   ├── 2025-09-15_event.ics   # Индивидуальный календарь события
│   ├── onevents-public.ics    # Общий календарь (все события)
│   └── onevents-public-moskva.ics  # Календарь по городу
├── rss/
│   └── rss.xml              # RSS лента событий
├── json/                    # JSON для импорта
│   ├── events.json          # Все события
│   ├── events_upcoming.json # Только предстоящие
│   ├── webinars.json        # Все вебинары
│   └── webinars_upcoming.json  # Предстоящие вебинары
└── img/                    # Изображения (копируются как есть)
```

---

## 📅 Как добавить событие?

### Вариант 1: Pull Request (рекомендуется)

1. Клонируйте репозиторий
2. Создайте новый файл в папке `events/` (или `webinars/` для вебинаров)
3. Заполните по шаблону (см. ниже)
4. Отправьте Pull Request

**Пример события (`events/example.yml`):**

```yaml
# Уникальный идентификатор (можно сгенерировать на https://guidgenerator.ru/)
id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Название события
title: "Название события"

# Дата в формате ГГГГ-ММ-ДД
date: "2025-09-15"

# Город проведения (или "Online"/"Онлайн")
city: "Москва"

# Адрес (для онлайн - пустая строка)
address: "ул. Арбат, 12"

# Имя файла картинки в папке img/events/
icon: "default.jpg"

# Краткое описание
description: "Описание события"

# Ссылка на регистрацию
registration_url: "https://example.com/register"

# Сессии (необязательно) - для многодневных событий
sessions:
  - date: "2025-09-15"     # Дата сессии
    start_time: "10:00"    # Время начала
    end_time: "18:00"      # Время окончания
```

### Вариант 2: Почта

Отправьте все данные события на: **info@onevents.ru**

---

## 🧪 Тестирование

Запустить тесты:

```bash
pytest
```

Тесты расположены в папке `tests/` и покрывают все основные модули проекта:

| Файл | Что проверяет |
|---|---|
| `test_text_utils.py` | Очистка текста от HTML-тегов, форматирование времени (HH:MM:SS), генерация слага |
| `test_utils_dates.py` | Склонение русских слов (день/дня/дней), форматирование месяцев, время до события |
| `test_url_utils.py` | Определение часового пояса по событию, сокращение ссылок, генерация ссылок на карты, добавление UTM-меток |
| `test_calendars.py` | Генерация VEVENT для простых событий и событий с сессиями, создание публичного ICS-календаря |
| `test_generator_calendars.py` | Генерация публичных календарей событий и вебинаров, создание индивидуальных ICS-файлов |
| `test_html.py` | Рендеринг карточек событий и вебинаров, генерация ID события, обработка необязательных полей |
| `test_rss.py` | Генерация RSS-ленты, сортировка, экранирование HTML, обработка пустой ленты и отсутствия URL регистрации |
| `test_json_export.py` | Сериализация событий и вебинаров в JSON, экспорт всех и предстоящих записей |
| `test_create_web.py` | Полная сборка сайта, обработка невалидных YAML-файлов |

---


## 📋 Команда

Проект создан и поддерживается сообществом 1С-разработчиков.
- Сайт: [https://onevents.ru](https://onevents.ru)
- Telegram: [t.me/OnEvents](https://t.me/OnEvents)
- Email: info@onevents.ru