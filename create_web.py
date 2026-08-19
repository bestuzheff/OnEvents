"""
Главный скрипт сборки сайта OnEvents.
Собирает YAML файлы событий и вебинаров, генерирует HTML, календари, RSS и JSON.
"""

import json
import re
import shutil
from datetime import date, datetime, timedelta
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
from webhtml import render_event, render_video_card, render_webinar
from webhtml.calendars import render_public_calendars, render_webinars_calendar

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

# Период "первого года" для страницы итогов (oneyear).
# Годовщина считается от начала (ровно год спустя), а показываем только то, что уже
# реально прошло: пока не наступила годовщина, конец периода — сегодняшняя дата сборки,
# чтобы все цифры и графики на странице честно совпадали с "N дней" в шапке.
ONEYEAR_START = date(2025, 8, 21)
ONEYEAR_ANNIVERSARY = date(ONEYEAR_START.year + 1, ONEYEAR_START.month, ONEYEAR_START.day)
ONEYEAR_END = min(ONEYEAR_ANNIVERSARY, date.today())

MONTH_SHORT_RU = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
MONTH_FULL_RU = [
    'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
    'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь',
]

ONLINE_CITIES = {'online', 'онлайн'}
DEFAULT_ICON = 'default.jpg'


def _parse_item_date(item: dict) -> date | None:
    """Дата мероприятия из YAML-записи или None, если поле отсутствует/битое."""
    try:
        return datetime.strptime(item['date'], '%Y-%m-%d').date()
    except (KeyError, ValueError):
        return None


def _is_online_city(city: str) -> bool:
    return not city or city.strip().lower() in ONLINE_CITIES


def _month_totals(counts_by_day: dict[date, int]) -> dict[tuple[int, int], int]:
    totals: dict[tuple[int, int], int] = {}
    for day, count in counts_by_day.items():
        key = (day.year, day.month)
        totals[key] = totals.get(key, 0) + count
    return totals


def _heatmap_cells_and_months(
    grid_start: date,
    weeks: int,
    counts_by_day: dict[date, int],
    month_totals: dict[tuple[int, int], int],
) -> tuple[list[dict], list[dict]]:
    """Ячейки сетки (по дням) и подписи месяцев (с шириной в колонках-неделях)."""
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

    return cells, months


def build_heatmap_data(all_events: list[dict], all_webinars: list[dict]) -> dict:
    """Считает реальное количество мероприятий по дням для тепловой карты oneyear.

    Возвращает данные в виде сетки календарных недель (столбцы) на 7 дней (строки),
    выровненной по понедельникам, с количеством мероприятий на день и итогом за месяц.
    """
    counts_by_day: dict[date, int] = {}
    for item in all_events + all_webinars:
        item_date = _parse_item_date(item)
        if item_date and ONEYEAR_START <= item_date <= ONEYEAR_END:
            counts_by_day[item_date] = counts_by_day.get(item_date, 0) + 1

    month_totals = _month_totals(counts_by_day)
    grid_start = ONEYEAR_START - timedelta(days=ONEYEAR_START.weekday())  # понедельник недели старта
    total_days = (ONEYEAR_END - grid_start).days + 1
    weeks = (total_days + 6) // 7

    cells, months = _heatmap_cells_and_months(grid_start, weeks, counts_by_day, month_totals)
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
    """Считает реальную разбивку мероприятий по месяцам (офлайн/онлайн/вебинары) для графика oneyear.

    Суммирует по номеру месяца без привязки к году, чтобы график шёл в привычном
    порядке январь → декабрь, даже когда период охватывает две календарные половины года.
    """
    buckets = {month: {'total': 0, 'offline': 0, 'online': 0, 'webinars': 0} for month in range(1, 13)}

    for item in all_events:
        item_date = _parse_item_date(item)
        if not item_date or not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        bucket = buckets[item_date.month]
        bucket['total'] += 1
        if _is_online_city(str(item.get('city', ''))):
            bucket['online'] += 1
        else:
            bucket['offline'] += 1

    for item in all_webinars:
        item_date = _parse_item_date(item)
        if not item_date or not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        bucket = buckets[item_date.month]
        bucket['total'] += 1
        bucket['webinars'] += 1

    return [{'label': MONTH_SHORT_RU[month - 1], **buckets[month]} for month in range(1, 13)]


def build_geo_data(all_events: list[dict], top_n: int = 8) -> list[dict]:
    """Считает реальное число офлайн-мероприятий по городам для графика географии oneyear."""
    counts: dict[str, int] = {}

    for item in all_events:
        item_date = _parse_item_date(item)
        if not item_date or not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        city = str(item.get('city', '')).strip()
        if _is_online_city(city):
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
    result = []

    for item in all_events:
        item_date = _parse_item_date(item)
        if not item_date or not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        city = str(item.get('city', '')).strip()
        if _is_online_city(city):
            continue
        result.append(
            {
                'title': item.get('title', ''),
                'city': city,
                'icon': '/img/events/' + item.get('icon', DEFAULT_ICON),
                'date': item['date'],
            }
        )

    return result


def build_recent_events(all_events: list[dict], all_webinars: list[dict], limit: int = 10) -> list[dict]:
    """Последние прошедшие мероприятия (события и вебинары) для oneyear."""
    today = date.today()
    items = []

    for item in all_events:
        item_date = _parse_item_date(item)
        if not item_date or item_date >= today:
            continue
        city = str(item.get('city', '')).strip()
        items.append(
            {
                'title': item.get('title', ''),
                'date': item['date'],
                'city': 'Онлайн' if _is_online_city(city) else city,
                'icon': '/img/events/' + item.get('icon', DEFAULT_ICON),
            }
        )

    for item in all_webinars:
        item_date = _parse_item_date(item)
        if not item_date or item_date >= today:
            continue
        items.append(
            {
                'title': item.get('title', ''),
                'date': item['date'],
                'city': 'Онлайн',
                'icon': '/img/webinars/' + item.get('pic', DEFAULT_ICON),
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


def _word_cloud_lemma(word: str) -> str | None:
    """Начальная форма слова для облака тегов или None, если слово нужно пропустить."""
    if word in WORD_CLOUD_STOPWORDS:
        return None
    if word != '1с' and len(word.replace('-', '')) < 3:
        return None
    lemma = word if word == '1с' else _morph.parse(word)[0].normal_form
    lemma = WORD_LEMMA_OVERRIDES.get(lemma, lemma)
    return None if lemma in WORD_CLOUD_STOPWORDS else lemma


def build_word_cloud(all_events: list[dict], all_webinars: list[dict], limit: int = 50) -> list[dict]:
    """Самые частые слова из названий и описаний мероприятий (для облака тегов).

    Разные формы одного слова (клуб/клуба, встреча/встречу, обсудим/обсудить)
    объединяются в начальную форму через морфологический анализ.
    """
    counts: dict[str, int] = {}

    for item in all_events + all_webinars:
        item_date = _parse_item_date(item)
        if not item_date or not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        text = (item.get('title', '') + ' ' + item.get('description', '')).lower()
        for word in WORD_RE.findall(text):
            lemma = _word_cloud_lemma(word)
            if lemma:
                counts[lemma] = counts.get(lemma, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{'text': word, 'count': count} for word, count in ranked]


def build_year_stats(all_events: list[dict], all_webinars: list[dict]) -> dict[str, int]:
    """Честные итоговые цифры для карточек в шапке oneyear (за период года)."""
    today = date.today()
    events_count = 0
    offline_count = 0
    cities: set[str] = set()
    videos_count = 0

    for item in all_events:
        item_date = _parse_item_date(item)
        if not item_date or not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        events_count += 1
        city = str(item.get('city', '')).strip()
        if not _is_online_city(city):
            offline_count += 1
            cities.add(city)
        if item_date < today and item.get('videos'):
            videos_count += 1

    webinars_count = 0
    for item in all_webinars:
        item_date = _parse_item_date(item)
        if not item_date or not (ONEYEAR_START <= item_date <= ONEYEAR_END):
            continue
        webinars_count += 1
        if item_date < today and item.get('videos'):
            videos_count += 1

    return {
        'total': events_count + webinars_count,
        'events': events_count,
        'webinars': webinars_count,
        'offline': offline_count,
        'cities': len(cities),
        'videos': videos_count,
    }


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
    year_stats = build_year_stats(all_events, all_webinars)
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
        .replace('{{ stat_total }}', str(year_stats['total']))
        .replace('{{ stat_events }}', str(year_stats['events']))
        .replace('{{ stat_webinars }}', str(year_stats['webinars']))
        .replace('{{ stat_cities }}', str(year_stats['cities']))
        .replace('{{ stat_offline }}', str(year_stats['offline']))
        .replace('{{ stat_videos }}', str(year_stats['videos']))
        .replace('{{ start_month }}', MONTH_FULL_RU[ONEYEAR_START.month - 1].upper())
        .replace('{{ start_day }}', str(ONEYEAR_START.day))
        .replace('{{ start_year }}', str(ONEYEAR_START.year))
        .replace('{{ end_month }}', MONTH_FULL_RU[ONEYEAR_END.month - 1].upper())
        .replace('{{ end_day }}', str(ONEYEAR_END.day))
        .replace('{{ end_year }}', str(ONEYEAR_END.year))
        .replace('{{ period_days }}', str((ONEYEAR_END - ONEYEAR_START).days))
        .replace('{{ period_days_label }}', ru_plural((ONEYEAR_END - ONEYEAR_START).days, 'день', 'дня', 'дней'))
        .replace('{{ meta_events_word }}', ru_plural(year_stats['total'], 'мероприятие', 'мероприятия', 'мероприятий'))
        .replace('{{ meta_cities_word }}', ru_plural(year_stats['cities'], 'город', 'города', 'городов'))
    )
    ONEYEAR_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    ONEYEAR_OUTPUT_FILE.write_text(oneyear_html, encoding='utf-8')


if __name__ == '__main__':
    main()
