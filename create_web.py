"""
Главный скрипт сборки сайта OnEvents.
Собирает YAML файлы событий и вебинаров, генерирует HTML, календари, RSS и JSON.
"""

import shutil
from datetime import date, datetime
from html import render_event, render_webinar
from html.calendars import render_public_calendars, render_webinars_calendar
from pathlib import Path

import yaml
from babel.dates import format_date

# Импорты из собственных модулей
from ics_calendars.generators import (
    generate_event_calendars,
    generate_public_calendars,
    generate_webinars_public_calendar,
)
from json_export import (
    export_events_to_json,
    export_upcoming_events_to_json,
    export_upcoming_webinars_to_json,
    export_webinars_to_json,
)
from rss import generate_rss

# Пути к директориям и файлам
EVENTS_DIR = Path('events')  # Папка с YAML файлами событий
WEBINARS_DIR = Path('webinars')  # Папка с YAML файлами вебинаров
TEMPLATE_FILE = Path('web/index.html')  # HTML шаблон сайта
OUTPUT_DIR = Path('site')  # Папка для собранного сайта
OUTPUT_FILE = OUTPUT_DIR / 'index.html'  # Итоговый HTML файл


def generate_sitemap() -> str:
    today_iso = date.today().isoformat()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://onevents.ru/</loc>
    <lastmod>{today_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://onevents.ru/rss/rss.xml</loc>
    <lastmod>{today_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>"""


def main() -> None:
    # Читаем HTML шаблон
    template = TEMPLATE_FILE.read_text(encoding='utf-8')

    # Списки для хранения событий
    all_events = []      # Все события (включая прошедшие)
    events = []          # Только предстоящие события для карточек
    all_webinars = []    # Все вебинары (включая прошедшие)
    webinars = []        # Только предстоящие вебинары для карточек

    # Читаем события из YAML файлов
    for file in EVENTS_DIR.glob('*.yml'):
        try:
            with open(file, encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Добавляем имя файла для формирования ID события
            data['filename'] = file.stem

            # Парсим дату события
            event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

            # Добавляем в соответствующие списки
            all_events.append(data)
            if event_date >= datetime.today().date():
                events.append(data)
        except Exception as e:
            print(f'Ошибка при чтении файла {file.name}: {e}')

    # Сортируем события по дате
    all_events.sort(key=lambda e: e['date'])
    events.sort(key=lambda e: e['date'])

    # Читаем вебинары из YAML файлов
    for file in WEBINARS_DIR.glob('*.yml'):
        try:
            with open(file, encoding='utf-8') as f:
                data = yaml.safe_load(f)

            data['filename'] = file.stem

            webinar_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            all_webinars.append(data)
            if webinar_date >= datetime.today().date():
                webinars.append(data)
        except Exception as e:
            print(f'Ошибка при чтении файла {file.name}: {e}')

    # Сортируем вебинары по дате
    all_webinars.sort(key=lambda e: e['date'])
    webinars.sort(key=lambda e: e['date'])

    # Создаем директорию для сайта
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Копируем статические файлы (картинки и иконки)
    shutil.copytree('img', 'site/img', dirs_exist_ok=True)
    shutil.copytree('icons', 'site/icons', dirs_exist_ok=True)

    # Генерируем ICS календари
    calendar_dir = OUTPUT_DIR / 'calendar'
    calendar_dir.mkdir(exist_ok=True)

    # Создаем индивидуальные календари для событий и вебинаров
    generate_event_calendars(events, calendar_dir)
    generate_event_calendars(webinars, calendar_dir)

    # Создаем публичные календари (общий и по городам)
    public_calendars = generate_public_calendars(all_events, calendar_dir)
    webinars_public_calendar_url = generate_webinars_public_calendar(
        all_webinars, calendar_dir
    )

    # Генерируем RSS ленту
    rss_dir = OUTPUT_DIR / 'rss'
    rss_dir.mkdir(exist_ok=True)
    rss_content = generate_rss(all_events)
    rss_file = rss_dir / 'rss.xml'
    rss_file.write_text(rss_content, encoding='utf-8')

    # Генерируем JSON файлы для импорта
    json_dir = OUTPUT_DIR / 'json'
    json_dir.mkdir(exist_ok=True)
    export_events_to_json(all_events, json_dir)           # Все события
    export_upcoming_events_to_json(events, json_dir)      # Предстоящие события
    export_webinars_to_json(all_webinars, json_dir)       # Все вебинары
    export_upcoming_webinars_to_json(webinars, json_dir)  # Предстоящие вебинары

    # Генерируем sitemap.xml
    sitemap_content = generate_sitemap()
    sitemap_file = OUTPUT_DIR / 'sitemap.xml'
    sitemap_file.write_text(sitemap_content, encoding='utf-8')

    # Генерируем robots.txt
    robots_content = 'User-agent: *\nAllow: /\nSitemap: https://onevents.ru/sitemap.xml\n'
    robots_file = OUTPUT_DIR / 'robots.txt'
    robots_file.write_text(robots_content, encoding='utf-8')

    # Генерируем HTML карточки событий и вебинаров
    events_html = '\n'.join(render_event(e) for e in events)
    webinar_html = '\n'.join(render_webinar(e) for e in webinars)
    public_calendars_html = render_public_calendars(public_calendars)
    webinars_calendar_html = render_webinars_calendar(webinars_public_calendar_url)

    # Форматируем дату сборки сайта
    today_date_str = format_date(date.today(), format='d MMMM y', locale='ru')

    # Заменяем плейсхолдеры в шаблоне на сгенерированный контент
    result_html = (
        template.replace('{{ events }}', events_html)
        .replace('{{ webinars }}', webinar_html)
        .replace('{{ public_calendars }}', public_calendars_html)
        .replace('{{ webinars_calendar }}', webinars_calendar_html)
        .replace('{{ builddate }}', today_date_str)
    )

    # Сохраняем готовый HTML файл
    OUTPUT_FILE.write_text(result_html, encoding='utf-8')


if __name__ == '__main__':
    main()
