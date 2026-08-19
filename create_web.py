"""
Главный скрипт сборки сайта OnEvents.
Собирает YAML файлы событий и вебинаров, генерирует HTML, календари, RSS и JSON.
"""

import json
import re
import shutil
from datetime import date, datetime, timedelta
from html import render_event, render_video_card, render_webinar
from html.calendars import render_public_calendars, render_webinars_calendar
from pathlib import Path

import pymorphy3
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
VIDEO_TEMPLATE_FILE = Path('web/video.html')  # HTML шаблон страницы видеозаписей
ONEYEAR_TEMPLATE_FILE = Path('web/oneyear.html')  # HTML шаблон страницы итогов года
OUTPUT_DIR = Path('site')  # Папка для собранного сайта
OUTPUT_FILE = OUTPUT_DIR / 'index.html'  # Итоговый HTML файл
VIDEO_OUTPUT_FILE = OUTPUT_DIR / 'video' / 'index.html'  # HTML файл страницы видеозаписей
ONEYEAR_OUTPUT_FILE = OUTPUT_DIR / 'oneyear' / 'index.html'  # HTML файл страницы итогов года

# Период "первого года" для страницы итогов (oneyear)
ONEYEAR_START = date(2025, 8, 21)
ONEYEAR_END = date(2026, 8, 21)

MONTH_SHORT_RU = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']


def build_heatmap_data(all_events: list[dict], all_webinars: list[dict]) -> dict:
    """Считает реальное количество мероприятий по дням для тепловой карты oneyear.

    Возвращает данные в виде сетки календарных недель (столбцы) на 7 дней (строки),
    выровненной по понедельникам, с количеством мероприятий на день и итогом за месяц.
    """
    counts_by_day: dict[date, int] = {}
    for item in all_events + all_webinars:
        try:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            continue
        if ONEYEAR_START <= item_date <= ONEYEAR_END:
            counts_by_day[item_date] = counts_by_day.get(item_date, 0) + 1

    month_totals: dict[tuple[int, int], int] = {}
    for day, count in counts_by_day.items():
        key = (day.year, day.month)
        month_totals[key] = month_totals.get(key, 0) + count

    grid_start = ONEYEAR_START - timedelta(days=ONEYEAR_START.weekday())  # понедельник недели старта
    total_days = (ONEYEAR_END - grid_start).days + 1
    weeks = (total_days + 6) // 7

    cells = []
    months = []
    current_month_key = None

    for week in range(weeks):
        column_month_key = None
        for row in range(7):
            day = grid_start + timedelta(days=week * 7 + row)
            in_range = ONEYEAR_START <= day <= ONEYEAR_END
            if row == 0:
                column_month_key = (day.year, day.month)
            cells.append(
                {
                    'date': day.isoformat(),
                    'count': counts_by_day.get(day, 0) if in_range else None,
                    'monthTotal': month_totals.get((day.year, day.month), 0),
                }
            )
        if column_month_key != current_month_key:
            months.append({'label': MONTH_SHORT_RU[column_month_key[1] - 1], 'span': 1})
            current_month_key = column_month_key
        else:
            months[-1]['span'] += 1

    return {'weeks': weeks, 'cells': cells, 'months': months}


def ru_plural(n: int, one: str, few: str, many: str) -> str:
    """Склонение числительного: 1 город, 2 города, 5 городов."""
    n_abs = abs(n)
    if n_abs % 10 == 1 and n_abs % 100 != 11:
        return one
    if 2 <= n_abs % 10 <= 4 and not (12 <= n_abs % 100 <= 14):
        return few
    return many


def month_range(start: date, end: date) -> list[tuple[int, int]]:
    """Список (год, месяц) от start до end включительно, по месяцам."""
    year, month = start.year, start.month
    result = []
    while (year, month) <= (end.year, end.month):
        result.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return result


def build_monthly_data(all_events: list[dict], all_webinars: list[dict]) -> list[dict]:
    """Считает реальную разбивку мероприятий по месяцам (офлайн/онлайн/вебинары) для графика oneyear."""
    online_cities = {'online', 'онлайн'}
    buckets = {
        ym: {'total': 0, 'offline': 0, 'online': 0, 'webinars': 0} for ym in month_range(ONEYEAR_START, ONEYEAR_END)
    }

    for item in all_events:
        try:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            continue
        if not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        key = (item_date.year, item_date.month)
        buckets[key]['total'] += 1
        city = str(item.get('city', '')).strip().lower()
        if city in online_cities:
            buckets[key]['online'] += 1
        else:
            buckets[key]['offline'] += 1

    for item in all_webinars:
        try:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            continue
        if not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        key = (item_date.year, item_date.month)
        buckets[key]['total'] += 1
        buckets[key]['webinars'] += 1

    return [
        {'label': MONTH_SHORT_RU[month - 1], 'year': year, **buckets[(year, month)]}
        for year, month in month_range(ONEYEAR_START, ONEYEAR_END)
    ]


def build_geo_data(all_events: list[dict], top_n: int = 8) -> list[dict]:
    """Считает реальное число офлайн-мероприятий по городам для графика географии oneyear."""
    online_cities = {'online', 'онлайн'}
    counts: dict[str, int] = {}

    for item in all_events:
        try:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            continue
        if not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        city = str(item.get('city', '')).strip()
        if not city or city.lower() in online_cities:
            continue
        counts[city] = counts.get(city, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top, rest = ranked[:top_n], ranked[top_n:]

    result = [{'city': city, 'count': count} for city, count in top]
    if rest:
        rest_word = ru_plural(len(rest), 'город', 'города', 'городов')
        result.append(
            {
                'city': f'Ещё {len(rest)} {rest_word}',
                'count': sum(count for _, count in rest),
                'cities': [{'city': city, 'count': count} for city, count in rest],
            }
        )
    return result


CITY_ARMS = {
    'Москва': 'moskva.png',
    'Санкт-Петербург': 'spb.png',
    'Новосибирск': 'novosibirsk.png',
    'Иркутск': 'irkutsk.png',
    'Владивосток': 'vladivostok.png',
    'Краснодар': 'krasnodar.png',
    'Ульяновск': 'ulyanovsk.png',
    'Воронеж': 'voronezh.png',
    'Екатеринбург': 'ekaterinburg.png',
    'Липецк': 'lipetsk.png',
    'Самара': 'samara.png',
    'Нижний Новгород': 'nizhny_novgorod.png',
    'Алматы': 'almaty.png',
    'Белгород': 'belgorod.png',
    'Оренбург': 'orenburg.png',
    'Светлогорск': 'svetlogorsk.png',
    'Омск': 'omsk.png',
    'Нячанг': 'nha_trang.png',
}


def build_city_arms() -> dict[str, str]:
    """Гербы/официальные эмблемы городов (только там, где они есть)."""
    return {city: f'/img/cities/{filename}' for city, filename in CITY_ARMS.items()}


# Резерв на случай городов, для которых герб плохо ложится в кружок —
# вместо картинки можно взять сплошную заливку официальным цветом.
CITY_COLORS: dict[str, str] = {}


def build_graph_data(all_events: list[dict]) -> list[dict]:
    """Список офлайн-мероприятий (город + логотип) для графа связей oneyear."""
    online_cities = {'online', 'онлайн'}
    result = []

    for item in all_events:
        try:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            continue
        if not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        city = str(item.get('city', '')).strip()
        if not city or city.lower() in online_cities:
            continue
        result.append(
            {
                'title': item.get('title', ''),
                'city': city,
                'icon': '/img/events/' + item.get('icon', 'default.jpg'),
                'date': item['date'],
            }
        )

    return result


def build_recent_events(all_events: list[dict], all_webinars: list[dict], limit: int = 10) -> list[dict]:
    """Последние прошедшие мероприятия (события и вебинары) для oneyear."""
    online_cities = {'online', 'онлайн'}
    today = date.today()
    items = []

    for item in all_events:
        try:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            continue
        if item_date >= today:
            continue
        city = str(item.get('city', '')).strip()
        items.append(
            {
                'title': item.get('title', ''),
                'date': item['date'],
                'city': 'Онлайн' if not city or city.lower() in online_cities else city,
                'icon': '/img/events/' + item.get('icon', 'default.jpg'),
            }
        )

    for item in all_webinars:
        try:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            continue
        if item_date >= today:
            continue
        items.append(
            {
                'title': item.get('title', ''),
                'date': item['date'],
                'city': 'Онлайн',
                'icon': '/img/webinars/' + item.get('pic', 'default.jpg'),
            }
        )

    items.sort(key=lambda x: x['date'], reverse=True)
    return items[:limit]


WORD_CLOUD_STOPWORDS = set(
    """
я мы ты вы он она оно они меня тебя его её нас вас их мне тебе ему ей нам вам им
мной тобой ими себя себе собой это эта этот эти эту этим этой тот та то те том
весь вся всё все всех всей всему всеми каждый каждая каждое каждые
свой своя своё свои наш наша наше наши который которая которое которые которых которым которой
что чтобы как так тоже также ещё уже очень более менее самый самая самое самые
и а но или либо да же ли бы не ни нет для от до из в во на по с со у о об обо
при про за над под между через без к ко если потому поэтому когда где куда
откуда зачем почему есть быть был была было были будет будут стать станет
можно нужно надо нельзя вот тут там здесь туда сюда снова опять только лишь
всегда никогда иногда обычно кто кого кому кем чей чья чьё чьи один одна одно
два три раз других другой другие кроме несколько мск
""".split()
)
# Слова, которые морфоанализатор не знает и неверно определяет как форму
# другого слова (обычно жаргон/бренды) — поправляем начальную форму вручную.
WORD_LEMMA_OVERRIDES = {
    'митапа': 'митап',
}
WORD_RE = re.compile(r'[а-яё]+(?:-[а-яё]+)*|1с')

_morph = pymorphy3.MorphAnalyzer()


def build_word_cloud(all_events: list[dict], all_webinars: list[dict], limit: int = 50) -> list[dict]:
    """Самые частые слова из названий и описаний мероприятий (для облака тегов).

    Разные формы одного слова (клуб/клуба, встреча/встречу, обсудим/обсудить)
    объединяются в начальную форму через морфологический анализ.
    """
    counts: dict[str, int] = {}

    for item in all_events + all_webinars:
        try:
            item_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            continue
        if not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        text = (item.get('title', '') + ' ' + item.get('description', '')).lower()
        for word in WORD_RE.findall(text):
            if word in WORD_CLOUD_STOPWORDS:
                continue
            if word != '1с' and len(word.replace('-', '')) < 3:
                continue
            lemma = word if word == '1с' else _morph.parse(word)[0].normal_form
            lemma = WORD_LEMMA_OVERRIDES.get(lemma, lemma)
            if lemma in WORD_CLOUD_STOPWORDS:
                continue
            counts[lemma] = counts.get(lemma, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{'text': word, 'count': count} for word, count in ranked]


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
    <loc>https://onevents.ru/video/</loc>
    <lastmod>{today_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://onevents.ru/rss/rss.xml</loc>
    <lastmod>{today_iso}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://onevents.ru/oneyear/</loc>
    <lastmod>{today_iso}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
</urlset>"""


def main() -> None:
    # Читаем HTML шаблон
    template = TEMPLATE_FILE.read_text(encoding='utf-8')

    # Списки для хранения событий
    all_events = []  # Все события (включая прошедшие)
    events = []  # Только предстоящие события для карточек
    all_webinars = []  # Все вебинары (включая прошедшие)
    webinars = []  # Только предстоящие вебинары для карточек

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
    shutil.copy('web/sw.js', OUTPUT_DIR / 'sw.js')

    # Генерируем ICS календари
    calendar_dir = OUTPUT_DIR / 'calendar'
    calendar_dir.mkdir(exist_ok=True)

    # Создаем индивидуальные календари для событий и вебинаров
    generate_event_calendars(events, calendar_dir)
    generate_event_calendars(webinars, calendar_dir)

    # Создаем публичные календари (общий и по городам)
    public_calendars = generate_public_calendars(all_events, calendar_dir)
    webinars_public_calendar_url = generate_webinars_public_calendar(all_webinars, calendar_dir)

    # Генерируем RSS ленту
    rss_dir = OUTPUT_DIR / 'rss'
    rss_dir.mkdir(exist_ok=True)
    rss_content = generate_rss(all_events)
    rss_file = rss_dir / 'rss.xml'
    rss_file.write_text(rss_content, encoding='utf-8')

    # Генерируем JSON файлы для импорта
    json_dir = OUTPUT_DIR / 'json'
    json_dir.mkdir(exist_ok=True)
    export_events_to_json(all_events, json_dir)  # Все события
    export_upcoming_events_to_json(events, json_dir)  # Предстоящие события
    export_webinars_to_json(all_webinars, json_dir)  # Все вебинары
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

    # Генерируем страницу видеозаписей
    today = datetime.today().date()

    video_items = []
    for event in all_events:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
        if event_date < today and event.get('videos'):
            video_items.append((event, 'event'))

    for webinar in all_webinars:
        webinar_date = datetime.strptime(webinar['date'], '%Y-%m-%d').date()
        if webinar_date < today and webinar.get('videos'):
            video_items.append((webinar, 'webinar'))

    video_items.sort(key=lambda x: x[0]['date'], reverse=True)
    video_cards_html = '\n'.join(
        render_video_card(ev, ev_type) for ev, ev_type in video_items
    )

    video_template = VIDEO_TEMPLATE_FILE.read_text(encoding='utf-8')
    video_html = (
        video_template
        .replace('{{ eventsvideo }}', video_cards_html)
        .replace('{{ builddate }}', today_date_str)
    )
    VIDEO_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    VIDEO_OUTPUT_FILE.write_text(video_html, encoding='utf-8')

    # Генерируем страницу итогов года
    heatmap_data = build_heatmap_data(all_events, all_webinars)
    monthly_data = build_monthly_data(all_events, all_webinars)
    geo_data = build_geo_data(all_events)
    graph_data = build_graph_data(all_events)
    recent_events = build_recent_events(all_events, all_webinars)
    word_cloud = build_word_cloud(all_events, all_webinars)
    oneyear_template = ONEYEAR_TEMPLATE_FILE.read_text(encoding='utf-8')
    oneyear_html = (
        oneyear_template.replace('{{ heatmap_data }}', json.dumps(heatmap_data, ensure_ascii=False))
        .replace('{{ monthly_data }}', json.dumps(monthly_data, ensure_ascii=False))
        .replace('{{ geo_data }}', json.dumps(geo_data, ensure_ascii=False))
        .replace('{{ graph_data }}', json.dumps(graph_data, ensure_ascii=False))
        .replace('{{ city_arms }}', json.dumps(build_city_arms(), ensure_ascii=False))
        .replace('{{ city_colors }}', json.dumps(CITY_COLORS, ensure_ascii=False))
        .replace('{{ recent_events }}', json.dumps(recent_events, ensure_ascii=False))
        .replace('{{ word_cloud }}', json.dumps(word_cloud, ensure_ascii=False))
    )
    ONEYEAR_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    ONEYEAR_OUTPUT_FILE.write_text(oneyear_html, encoding='utf-8')


if __name__ == '__main__':
    main()
