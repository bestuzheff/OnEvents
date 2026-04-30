[![OpenYellow](https://img.shields.io/endpoint?url=https://openyellow.org/data/badges/7/1040948355.json)](https://openyellow.org/grid?data=top&repo=1040948355)
[![Quality Gate Status](https://sonar.openbsl.ru/api/project_badges/measure?project=onevents&metric=alert_status)](https://sonar.openbsl.ru/dashboard?id=onevents)
[![Telegram](https://img.shields.io/badge/telegram-%D0%BA%D0%B0%D0%BD%D0%B0%D0%BB-blue.svg?label=telegram)](https://t.me/OnEvents)
[![LICENSE](https://img.shields.io/github/license/crimsongoldteam/md_design?label=%D0%BB%D0%B8%D1%86%D0%B5%D0%BD%D0%B7%D0%B8%D1%8F)](https://github.com/bestuzheff/OnEvents/blob/main/LICENSE)

# 🎉 OnEvents

## Адрес проета: [https://onevents.ru](https://onevents.ru)

## ❓ Зачем всё это?

Мы решили собрать все события, связанные с **1С**, в одном месте.  
Многие из нас регулярно бывают в разных городах — по работе или просто отдыхая.  
И здорово, если именно в это время где-то рядом проходит мероприятие по 1С: можно заглянуть, познакомиться с коллегами и узнать что-то новое.  

---

## ⚙️ Сборка проекта

### 🐳 Самый простой способ — через Docker
```bash
docker build -t onevents .
docker run --rm -p 8080:80 onevents
```
После запуска проект будет доступен по ссылке 👉 [http://localhost:8080](http://localhost:8080)

### 🐍 Второй способ — через Python
Для этого понадобится установленный [Python](https://www.python.org/).

1. Создаём виртуальное окружение:  
   ```bash
   python -m venv .venv
   ```

2. Активируем его:  
   - CMD:  
     ```bash
     .venv\Scripts\activate.bat
     ```
   - PowerShell:  
     ```bash
     .venv\Scripts\activate.ps1
     ```
   - Linux / macOS:  
     ```bash
     source .venv/bin/activate
     ```

3. Устанавливаем зависимости:  
   ```bash
   pip install -r requirements.txt
   ```

4. Запускаем сборку:  
   ```bash
   python create_web.py
   ```

📂 В папке `site` появится собранный проект.

---

## 📅 Как добавить событие?

Есть два способа:

### ✍️ Способ первый — Pull Request
1. Клонировать репозиторий;  
2. В папке `events` создать новый файл с описанием события (для удобства есть шаблон `event_template.yml`). Имя файла любое, главное — уникальное;  
3. Сделать **Pull Request**;  
4. После проверки и принятия событие появится на сайте.

Пример события (`.yml`):  
```yaml
id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" # Уникальный идентификатор события (можно сгенерировать на сайте https://guidgenerator.ru/)
title: "Название события" # Название события
date: "2025-09-15" # Дата начала события, формат YYYY-MM-DD
city: "Москва" # Город, где будет проходить событие (либо Online)
address: "ул. Арбат, 12" # Адрес проведения (Если форма проведения Online, то адрес пустой)
icon: "default.jpg" # Файл с логотипом (если нет то default.jpg)
description: "Краткое описание события, чтобы сразу понять, о чем оно." # Краткое описание
registration_url: "https://example.com/register" # Ссылка на регистрацию
sessions: # Время проведения события (не обязательная секция, используется для формирования календаря)
  - date: "2025-09-15"   # Дата проведения
    start_time: "10:00"  # Время начала события
    end_time: "18:00"    # Врмя окончания события
  - date: "2025-09-16"   # Дата проведения
    start_time: "11:00"  # Время начала события
    end_time: "17:30"    # Врмя окончания события
```

### 📧 Способ второй — через почту
Просто прислать все данные о событии на почту 👉 **info@onevents.ru**

---

## 🚀 Что дальше?

~~Дальше проект будет переписываться на [ОСень](https://github.com/autumn-library/autumn) и [Вино](https://github.com/autumn-library/winow).~~
~~Почему так? Потому что [Untru](https://github.com/Untru) сказал, что это правильно.~~
~~А кто я такой, чтобы с ним спорить 😁~~

По просьбам трудящихся остаемся на Python🐍!
1С всем и на работе хватает…

