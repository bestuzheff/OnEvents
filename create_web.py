import yaml
from datetime import datetime, date, timezone
from email.utils import format_datetime
import xml.sax.saxutils as saxutils
from pathlib import Path
from babel.dates import format_date
import shutil
import hashlib
import requests
import pytz

from utils.text import clean_text, make_slug, to_hhmmss, SAFE_CHARS_PATTERN, DASHES_SPACES_PATTERN

# Пути
EVENTS_DIR = Path("events")
WEBINARS_DIR = Path("webinars")
TEMPLATE_FILE = Path("web/index.html")
OUTPUT_DIR = Path("site")
OUTPUT_FILE = OUTPUT_DIR / "index.html"

# Загружаем шаблон
template = TEMPLATE_FILE.read_text(encoding="utf-8")

# Список событий
all_events = []    # все события (включая прошедшие)
events = []        # только будущие события для карточек/индивидуальных .ics
all_webinars = []  # все вебинары (включая прошедшие)
webinars = []      # только будущие вебинары для карточек/индивидуальных .ics

#######################################################
# Заполняем события
for file in EVENTS_DIR.glob("*.yml"):
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Добавляем имя файла к данным события (без расширения .yml)
    data['filename'] = file.stem
    
    event_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    all_events.append(data)
    if event_date >= datetime.today().date():
        events.append(data)

# Сортируем по дате
all_events.sort(key=lambda e: e["date"])  # для общего календаря
events.sort(key=lambda e: e["date"])      # для карточек/индивидуальных .ics

#######################################################
# Заполняем вебинары
for file in WEBINARS_DIR.glob("*.yml"):
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Добавляем имя файла к данным вебинара (без расширения .yml)
    data['filename'] = file.stem
    
    webinar_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    all_webinars.append(data)
    if webinar_date >= datetime.today().date():
        webinars.append(data)

# Сортируем по дате
all_webinars.sort(key=lambda e: e["date"])  # для общего календаря
webinars.sort(key=lambda e: e["date"])      # для карточек/индивидуальных .ics


# Функция для сокращения ссылок через clck.ru
def shorten_url(url: str) -> str:
    """Сокращает URL через сервис clck.ru"""
    
    if not url:
        return url
    
    try:
        response = requests.get('https://clck.ru/--', params={'url': url}, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        else:
            # Если сервис недоступен, возвращаем оригинальную ссылку
            return url
    except Exception:
        # В случае любой ошибки возвращаем оригинальную ссылку
        return url

# Функция возвращает таймзону для события на основе города
def get_timezone_for_event(event: dict):
    """Возвращает таймзону для события на основе города."""
    tz_moscow = "Europe/Moscow"
    timezones = {
        "online": tz_moscow,
        "онлайн": tz_moscow,
        "санкт-петербург": tz_moscow,
        "москва": tz_moscow,
        "новосибирск": "Asia/Novosibirsk",
        "иркутск": "Asia/Irkutsk",
    }   

    city = str(event.get('city', '')).strip().lower()
    return timezones.get(city)

# Функция для создания ссылки на Яндекс.Карты
def map_link(city: str, address: str = "") -> str:
    """Создает ссылку на Яндекс.Карты"""
    
    # Не показываем если адрес пустой
    if not address: 
        return ""

    # Не показываем для онлайн событий
    if city.lower() in ['online', 'онлайн']:
        return ""
    
    # Не показываем если в адресе есть слова о неопределенности
    uncertain_words = ['уточняется', 'придумано', 'объявлено', 'уточнить', 'tbd', 'tba', 'todo']
    if any(word in address.lower() for word in uncertain_words):
        return ""
    
    full_address = f"{city}, {address}"
    
    # URL-кодируем адрес для безопасной передачи в URL
    import urllib.parse
    encoded_address = urllib.parse.quote(full_address)
    
    return f"https://yandex.ru/maps/?text={encoded_address}"

# Функция для добавления UTM меток к ссылкам регистрации
def add_utm_marks(url: str) -> str:
    """Добавляет UTM метки к ссылке регистрации, если их там нет"""
    if not url or 'utm_source=' in url:
        return url

    # Список URL, которые не нужно обрабатывать
    exclude_urls = [
        't.me',
        'telegram.org'
    ]
    if any(exclude in url for exclude in exclude_urls):
        return url
    
    # Определяем разделитель (если в URL уже есть параметры)
    separator = '&' if '?' in url else '?'
    
    # UTM метки для отслеживания трафика с сайта onevents.ru
    utm_source = 'onevents.ru'        # Источник трафика - наш сайт
    utm_medium = 'website'            # Канал - веб-сайт (не email, не соцсети)
    utm_campaign = 'news'             # Кампания - новости/события
    utm_content = 'link'              # Контент - ссылка на регистрацию
    
    # Собираем все UTM параметры в одну строку
    utm_params = f"{separator}utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}&utm_content={utm_content}"
    
    return url + utm_params

def generate_event_vevent(event, session=None, session_index=None):
    """Генерирует VEVENT для события или сессии"""
    # Создаем уникальный UID на основе всех ключевых характеристик события
    # Используем более детальную строку для генерации UID
    uid_components = [
        event['title'],
        event['date'],
        event.get('city', ''),
        event.get('address', ''),
        event.get('url', ''),
        event.get('registration_url', '')
    ]
    
    if session_index is not None:
        # Для сессий добавляем информацию о сессии
        session_info = f"{session['date']}-{session['start_time']}-{session['end_time']}"
        uid_components.append(session_info)
        uid_components.append(str(session_index))
    
    # Создаем строку для хеширования, убирая лишние пробелы и нормализуя
    uid_string = '-'.join(str(comp).strip() for comp in uid_components if comp)
    uid = hashlib.md5(uid_string.encode('utf-8')).hexdigest() # NOSONAR
    
    # Формируем адрес
    location = event.get('city', '')
    if not location:
        location = "Online"

    address = event.get('address')
    if address:  # проверяет на None и «ложные» значения
        location += f", {address}"
    
    title = clean_text(event['title'])
    description = clean_text(event['description'])
    
    tzid = get_timezone_for_event(event)
    tz_param = f";TZID={tzid}" if tzid else ""

    if session:
        # Сессия события
        session_date = datetime.strptime(session['date'], "%Y-%m-%d")
        
        # Формируем время начала и окончания
        start_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['start_time'])}"
        end_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['end_time'])}"
        
        # Название сессии с датой
        date_str = format_date(session_date, format="d MMMM", locale="ru")
        session_title = f"{title} ({date_str})"
        
        
        # Добавляем короткую ссылку на карту если есть
        map_url = shorten_url(map_link(event.get('city', ''), event.get('address', '')))
        map_text = ""
        if map_url:
            map_text = f"\\n\\nПоказать на карте: {map_url}"
        
        registration_link = event.get('registration_url') or event.get('url', '')
        description_text = (
            f"{description}\\n\\nСсылка: {registration_link}"
            f"\\n\\nВремя: {session['start_time']}-{session['end_time']}{map_text}"
        )
        
        return f"""BEGIN:VEVENT
UID:{uid}@onevents.ru
DTSTART{tz_param}:{start_datetime}
DTEND{tz_param}:{end_datetime}
SUMMARY:{session_title}
DESCRIPTION:{description_text}
LOCATION:{location}
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT"""
    else:
        # Обычное однодневное событие
        event_date = datetime.strptime(event['date'], "%Y-%m-%d")
        
         
        # Добавляем ссылку на карту если есть
        map_url = shorten_url(map_link(event['city'], event['address']))
        map_text = ""
        if map_url:
            map_text = f"\\n\\nПоказать на карте: {map_url}"
        
        registration_link = event.get('registration_url') or event.get('url', '')
        description_text = (
            f"{description}\\n\\nСсылка: {registration_link}{map_text}"
        )
        
        return f"""BEGIN:VEVENT
UID:{uid}@onevents.ru
DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}
SUMMARY:{title}
DESCRIPTION:{description_text}
LOCATION:{location}
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT"""

# Функция генерации общего календаря со всеми событиями
def generate_public_calendar(events, calendar_name: str | None = None, wr_url: str | None = None):
    """Генерирует общий календарь со всеми событиями.

    calendar_name: заголовок календаря для X-WR-CALNAME
    wr_url: значение для X-WR-URL (публичная ссылка на файл)
    """
    
    # Текущее время для метаданных
    now = datetime.now()
    now_str = now.strftime('%Y%m%dT%H%M%SZ')
    
    default_name = "Cобытия 1C - OnEvents"
    cal_name = calendar_name or default_name
    cal_url = wr_url

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//OnEvents//OnEvents Calendar//RU
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:{cal_name}
X-WR-CALDESC:Календарь 1С событий от OnEvents
X-WR-TIMEZONE:Europe/Moscow
X-WR-URL:{cal_url}
REFRESH-INTERVAL;VALUE=DURATION:PT1H
X-PUBLISHED-TTL:PT1H
LAST-MODIFIED:{now_str}
DTSTAMP:{now_str}"""
    
    # Добавляем все события в календарь
    for event in events:
        # Проверяем, есть ли секция sessions для события
        if 'sessions' in event and event['sessions']:
            sessions = event['sessions']
            # Сортируем сессии по дате
            sessions.sort(key=lambda x: x['date'])
            
            # Создаем отдельный VEVENT для каждой сессии
            for i, session in enumerate(sessions):
                vevent = generate_event_vevent(event, session, i + 1)
                ics_content += f"\n{vevent}"
        else:
            # Обычное однодневное событие
            vevent = generate_event_vevent(event)
            ics_content += f"\n{vevent}"
    
    ics_content += """
END:VCALENDAR"""
    
    return ics_content

# Функция генерации ICS файла для события
def generate_ics_content(event):
    """Генерирует содержимое .ics файла для события"""
    
    # Формируем ICS содержимое
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//OnEvents//OnEvents Calendar//RU
CALSCALE:GREGORIAN
METHOD:PUBLISH"""

    tzid = get_timezone_for_event(event)
    if tzid:
        ics_content += f"""
X-WR-TIMEZONE:{tzid}"""
    
    # Проверяем, есть ли секция sessions для события
    if 'sessions' in event and event['sessions']:
        sessions = event['sessions']
        # Сортируем сессии по дате
        sessions.sort(key=lambda x: x['date'])
        
        # Создаем отдельный VEVENT для каждой сессии
        for i, session in enumerate(sessions):
            vevent = generate_event_vevent(event, session, i + 1)
            ics_content += f"\n{vevent}"
    else:
        # Обычное однодневное событие
        vevent = generate_event_vevent(event)
        ics_content += f"\n{vevent}"
    
    ics_content += """
END:VCALENDAR"""
    
    return ics_content

# Функция генерации публичных календарей
def generate_public_calendars(all_events, calendar_dir):
    """Генерирует все публичные календари и возвращает список кортежей (название, ссылка, город)"""
    
    public_calendars = []
    
    # Генерируем общий календарь со всеми событиями
    public_calendar_url = "https://onevents.ru/calendar/onevents-public.ics"
    public_calendar_content = generate_public_calendar(
        all_events,
        calendar_name="События 1С - OnEvents",
        wr_url=public_calendar_url,
    )
    public_calendar_path = calendar_dir / "onevents-public.ics"
    public_calendar_path.write_text(public_calendar_content, encoding="utf-8")
    
    # Добавляем общий календарь в список
    public_calendars.append(("Все города", public_calendar_url, ""))
    
    # Генерируем отдельные публичные календари по городам
    unique_cities = sorted({e.get('city', '').strip() for e in all_events if e.get('city')})
    for city in unique_cities:
        city_events = [e for e in all_events if e.get('city') == city]
        city_slug = make_slug(city)
        city_filename = f"onevents-public-{city_slug}.ics"
        city_url = f"https://onevents.ru/calendar/{city_filename}"
        city_calendar_name = f"События 1С. {city} - OnEvents"
        
        city_calendar_content = generate_public_calendar(
            city_events,
            calendar_name=city_calendar_name,
            wr_url=city_url,
        )
        (calendar_dir / city_filename).write_text(city_calendar_content, encoding="utf-8")
        
        # Сохраняем информацию о календаре
        public_calendars.append((city, city_url, city))
    
    return public_calendars


def generate_webinars_public_calendar(all_webinars, calendar_dir):
    """Генерирует отдельный публичный календарь для раздела «Прямой эфир» и возвращает ссылку на него"""
    
    webinars_calendar_url = "https://onevents.ru/calendar/onevents-webinars.ics"
    webinars_calendar_content = generate_public_calendar(
        all_webinars,
        calendar_name="Прямой эфир — OnEvents",
        wr_url=webinars_calendar_url,
    )
    webinars_calendar_path = calendar_dir / "onevents-webinars.ics"
    webinars_calendar_path.write_text(webinars_calendar_content, encoding="utf-8")
    
    return webinars_calendar_url

# Функция генерации HTML блока публичных календарей
def render_public_calendars(public_calendars: list[tuple[str, str, str]]):
    """Генерирует HTML блок с публичными календарями"""
    
    calendars_html = []
    for name, url, city in public_calendars:
        calendars_html.append(f"""
    <div class="calendar-item" data-city="{city}">
        <div class="calendar-city-name">{name}</div>
        <div class="calendar-input-group">
            <input type="text" class="calendar-input" value="{url}" readonly>
            <button class="calendar-copy-btn" title="Копировать ссылку">🔗</button>
        </div>
    </div>""")
    
    return f"""
    <h2>🔗 Подписка на календарь</h2>
    
    <article class="card">
        <p>Чтобы всегда быть в курсе событий подпишитесь на календарь в вашем приложении-календаре. События будут автоматически обновляться при добавлении на сайт.</p>
        <ol>
            <li>Скопируйте ссылку календаря</li>
            <li>В приложении календаря выберите "Добавить календарь подписки" (для Apple) или "Добавить календарь по URL" (для Google)</li>
        </ol>
        {''.join(calendars_html)}
    </article>
    """


def render_webinars_calendar(webinars_calendar_url: str):
    """Генерирует HTML блок подписки на календарь для Прямого эфира (вебинаров)"""
    
    return f"""
    <article class="card">
        <p>Подпишитесь на отдельный календарь с вебинарами из раздела «Прямой эфир».</p>
        <div class="calendar-item" data-city="">
            <div class="calendar-city-name">Прямой эфир</div>
            <div class="calendar-input-group">
                <input type="text" class="calendar-input" value="{webinars_calendar_url}" readonly>
                <button class="calendar-copy-btn" title="Копировать ссылку">🔗</button>
            </div>
        </div>
    </article>
    """

# Функция генерации календаря для события
def generate_event_calendars(events, calendar_dir):
    """Генерирует .ics файлы для каждого события"""
    
    for event in events:
        # Генерируем имя файла для .ics
        safe_title = SAFE_CHARS_PATTERN.sub('', event['title']).strip()
        safe_title = DASHES_SPACES_PATTERN.sub('-', safe_title)
        ics_filename = f"{event['date']}-{safe_title}.ics"
        
        # Генерируем содержимое .ics файла
        ics_content = generate_ics_content(event)
        
        # Сохраняем .ics файл
        ics_file_path = calendar_dir / ics_filename
        ics_file_path.write_text(ics_content, encoding="utf-8")

# Функция генерации ID события для якорных ссылок
def generate_event_id(event, type):
    """Генерирует уникальный ID для события на основе имени файла"""
    # Используем имя файла как основу для ID (оно уже содержит дату и краткое описание)
    return f"{type}-{event['filename']}"

# Функция генерации карточки события
def render_event(e):
    date_obj = datetime.strptime(e['date'], "%Y-%m-%d")
    date_str = date_str = format_date(date_obj, format="d MMMM y", locale="ru")  # 15 сентября 2025
    
    
    if len(e['address']) == 0:
      address_str  = e['city']
    else:
      address_str  = e['city'] + ", "  + e['address']
    
    # Генерируем имя файла для .ics
    safe_title = SAFE_CHARS_PATTERN.sub('', e['title']).strip()
    safe_title = DASHES_SPACES_PATTERN.sub('-', safe_title)
    ics_filename = f"{e['date']}-{safe_title}.ics"
    
    # Добавляем UTM метки к ссылке регистрации
    registration_url_with_utm = add_utm_marks(e['registration_url'])
    
    # Генерируем уникальный ID для события
    event_id = generate_event_id(e, "event")
    
    # Добавляем ссылку на карту
    map_url = map_link(e['city'], e['address'])
    map_link_html = ""
    if map_url:
        map_link_html = f' <a href="{map_url}" target="_blank" class="map-link" title="Показать на карте">Показать на карте</a>'

    return f"""
    <article class="card" itemscope itemtype="https://schema.org/Event" data-city="{e['city']}" id="{event_id}">
      <div class="card-header">
        <div class="card-header-main">
          <img class="logo-img" alt="Логотип «{e['title']}»" 
               src="img/events/{e['icon']}" width="72" height="72" 
               style="border-radius:15%; object-fit:cover;">
          <div class="event-info">
            <h2 class="card-title" itemprop="name" style="margin:0 0 .25em 0;">{e['title']}</h2>
            <div class="meta-item">
              <span class="icon">📅</span>
              <time itemprop="startDate" datetime="{e['date']}">{date_str}</time>
            </div>
            <div class="meta-item">
              <span class="icon">📌</span>
              <span itemprop="location" itemscope itemtype="https://schema.org/Place">
                <span itemprop="addressLocality">{address_str}</span>
              </span>
            </div>{map_link_html}
          </div>
        </div>
        <button class="event-copy-btn" data-event-id="{event_id}" title="Копировать ссылку на событие">🔗</button>
      </div>
      <p>{e['description']}</p>
      <div class="event-actions">
        <a href="{registration_url_with_utm}" role="button" target="_blank">Регистрация</a>
        <a href="calendar/{ics_filename}" role="button" download="{ics_filename}">Добавить в календарь</a>
      </div>
    </article>
    """

# Функция генерации карточки вебинара
def render_webinar(e):
    date_obj = datetime.strptime(e['date'], "%Y-%m-%d")
    date_str = date_str = format_date(date_obj, format="d MMMM y", locale="ru")  # 15 сентября 2025
        
    # Генерируем имя файла для .ics
    safe_title = SAFE_CHARS_PATTERN.sub('', e['title']).strip()
    safe_title = DASHES_SPACES_PATTERN.sub('-', safe_title)
    ics_filename = f"{e['date']}-{safe_title}.ics"
    
    # Добавляем UTM метки к ссылке регистрации
    translation_url = e['url']
    
    # Генерируем уникальный ID для события
    webinar_id = generate_event_id(e, "webinar")
    
    return f"""
    <article class="card" itemscope itemtype="https://schema.org/Event" id="{webinar_id}">
      <div class="card-header">
        <div class="card-header-main">
          <img class="logo-img" alt="Логотип «{e['title']}»" src="img/webinars/{e['pic']}" width="256">
          <div class="event-info">
            <h2 class="card-title" itemprop="name" style="margin:0 0 .25em 0;">{e['title']}</h2>
            <div class="meta-item">
              <span class="icon">📅</span>
              <time itemprop="startDate" datetime="{e['date']}">{date_str}</time>
            </div>
            {e['description']}
            <div class="event-actions">
              <a href="{translation_url}" role="button" target="_blank">Трансляция</a>
              <a href="calendar/{ics_filename}" role="button" download="{ics_filename}">Добавить в календарь</a>
            </div>
          </div>
        </div>
        <button class="event-copy-btn" data-event-id="{webinar_id}" title="Копировать ссылку на событие">🔗</button>
      </div>
    </article>
    """    


# Функция генерации RSS ленты
def generate_rss(all_events):
    """Генерирует общий RSS со всеми событиями"""

    site_url = "https://onevents.ru"
    rss_url = f"{site_url}/rss/rss.xml"
    rss_items = []
    now = datetime.now(timezone.utc)

    # Для RSS события должны идти от свежего к прошедшему
    all_events = sorted(all_events, key=lambda e: e["date"], reverse=True)
    for event in all_events:
        tz_name = get_timezone_for_event(event) or "Europe/Moscow"
        tz = pytz.timezone(tz_name)
        event_date = datetime.strptime(event["date"], "%Y-%m-%d")
        event_date = event_date.replace(tzinfo=tz)
        pub_date = format_datetime(event_date)

        event_id = generate_event_id(event, "event")
        event_link = f"{site_url}/#{event_id}"

        title = saxutils.escape(event["title"])
        description_text = (
            f"{event['description']}\n\n"
            f"Дата: {format_date(event_date.date(), format='d MMMM y', locale='ru')}\n"
            f"Место: {event['city']}"
        )

        if event.get("registration_url"):
            description_text += f"\nРегистрация: {event['registration_url']}"

        guid = f"onevents-{event['filename']}"

        rss_items.append(f"""
        <item>
            <title>{title}</title>
            <link>{event_link}</link>
            <guid isPermaLink="false">{guid}</guid>
            <pubDate>{pub_date}</pubDate>
            <description>{saxutils.escape(description_text)}</description>
        </item>
        """)

    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"
        xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>События 1С — OnEvents</title>
        <link>{site_url}</link>
        <atom:link href="{rss_url}" rel="self" type="application/rss+xml" />
        <description>Все события 1С от OnEvents</description>
        <language>ru</language>
        <lastBuildDate>{format_datetime(now)}</lastBuildDate>
        <generator>OnEvents</generator>
        {''.join(rss_items)}
    </channel>
    </rss>
    """

    return rss_content

# Создаем папку site при необходимости
OUTPUT_DIR.mkdir(exist_ok=True)

# Копируем картинки
shutil.copytree("img", "site/img", dirs_exist_ok=True)

# Копируем Иконки
shutil.copytree("icons", "site/icons", dirs_exist_ok=True)

# Создаем календари
calendar_dir = OUTPUT_DIR / "calendar"
calendar_dir.mkdir(exist_ok=True)

generate_event_calendars(events, calendar_dir)
generate_event_calendars(webinars, calendar_dir)
public_calendars = generate_public_calendars(all_events, calendar_dir)
webinars_public_calendar_url = generate_webinars_public_calendar(all_webinars, calendar_dir)

# Генерируем RSS
rss_dir = OUTPUT_DIR / "rss"
rss_dir.mkdir(exist_ok=True)
rss_content = generate_rss(all_events)
rss_file = rss_dir / "rss.xml"
rss_file.write_text(rss_content, encoding="utf-8")

# Генерируем HTML
events_html = "\n".join(render_event(e) for e in events)
webinar_html = "\n".join(render_webinar(e) for e in webinars)
public_calendars_html = render_public_calendars(public_calendars)
webinars_calendar_html = render_webinars_calendar(webinars_public_calendar_url)

# Подставляем в шаблон
today_date_str = format_date(date.today(), format="d MMMM y", locale="ru")
result_html = (
    template
    .replace("{{ events }}", events_html)
    .replace("{{ webinars }}", webinar_html)
    .replace("{{ public_calendars }}", public_calendars_html)
    .replace("{{ webinars_calendar }}", webinars_calendar_html)
    .replace("{{ builddate }}", today_date_str)
)

# Сохраняем результат
OUTPUT_FILE.write_text(result_html, encoding="utf-8")