import os
import yaml
from datetime import datetime, date
from pathlib import Path
from babel.dates import format_date
import shutil
import hashlib
import re

# Общие регулярные выражения
SAFE_CHARS_PATTERN = re.compile(r'[^\w\s-]')
DASHES_SPACES_PATTERN = re.compile(r'[-\s]+')

# Пути
EVENTS_DIR = Path("events")
TEMPLATE_FILE = Path("web/index.html")
OUTPUT_DIR = Path("site")
OUTPUT_FILE = OUTPUT_DIR / "index.html"

# Загружаем шаблон
template = TEMPLATE_FILE.read_text(encoding="utf-8")

# Список событий
all_events = []  # все события (включая прошедшие)
events = []      # только будущие события для карточек/индивидуальных .ics

for file in EVENTS_DIR.glob("*.yml"):
    with open(file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    event_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    all_events.append(data)
    if event_date >= datetime.today().date():
        events.append(data)

# Сортируем по дате
all_events.sort(key=lambda e: e["date"])  # для общего календаря
events.sort(key=lambda e: e["date"])      # для карточек/индивидуальных .ics

# Функция для добавления UTM меток к ссылкам регистрации
def add_utm_marks(url: str) -> str:
    """Добавляет UTM метки к ссылке регистрации, если их там нет"""
    if not url or 'utm_source=' in url:
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

# Вспомогательные функции для работы с ICS
def to_hhmmss(time_str: str) -> str:
    """Нормализует время к формату HHMMSS для ICS"""
    s = str(time_str).strip()
    s = s.replace('.', ':')
    parts = s.split(':')
    if len(parts) == 1:
        hour = parts[0]
        minute = '00'
    else:
        hour = parts[0]
        minute = parts[1]
    hour = hour.zfill(2)
    minute = minute.zfill(2)
    return f"{hour}{minute}00"

def clean_text(text):
    """Очищает текст от HTML и экранирует специальные символы для ICS"""
    # Убираем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    # Экранируем специальные символы для ICS
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    return text

def make_slug(text: str) -> str:
    """Готовит безопасный слаг для имени файла из названия города."""
    safe = SAFE_CHARS_PATTERN.sub('', str(text)).strip()
    safe = DASHES_SPACES_PATTERN.sub('-', safe)
    return safe.lower()

def generate_event_vevent(event, session=None, session_index=None):
    """Генерирует VEVENT для события или сессии"""
    # Создаем уникальный UID на основе всех ключевых характеристик события
    # Используем более детальную строку для генерации UID
    uid_components = [
        event['title'],
        event['date'],
        event['city'],
        event.get('address', ''),
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
    location = event['city']
    if event['address']:
        location += f", {event['address']}"
    
    title = clean_text(event['title'])
    description = clean_text(event['description'])
    
    if session:
        # Сессия события
        session_date = datetime.strptime(session['date'], "%Y-%m-%d")
        
        # Формируем время начала и окончания
        start_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['start_time'])}"
        end_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['end_time'])}"
        
        # Название сессии с датой
        date_str = format_date(session_date, format="d MMMM", locale="ru")
        session_title = f"{title} ({date_str})"
        
        # Добавляем UTM метки к ссылке регистрации для ICS
        registration_url_with_utm = add_utm_marks(event['registration_url'])
        
        description_text = (
            f"{description}\\n\\nСсылка на регистрацию: {registration_url_with_utm}"
            f"\\n\\nВремя: {session['start_time']}-{session['end_time']}"
        )
        
        return f"""BEGIN:VEVENT
UID:{uid}@onevents.ru
DTSTART:{start_datetime}
DTEND:{end_datetime}
SUMMARY:{session_title}
DESCRIPTION:{description_text}
LOCATION:{location}
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT"""
    else:
        # Обычное однодневное событие
        event_date = datetime.strptime(event['date'], "%Y-%m-%d")
        
        # Добавляем UTM метки к ссылке регистрации для ICS
        registration_url_with_utm = add_utm_marks(event['registration_url'])
        
        description_text = (
            f"{description}\\n\\nСсылка на регистрацию: {registration_url_with_utm}"
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
            <button class="calendar-copy-btn" title="Копировать ссылку">📋</button>
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

# Функция генерации карточки
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
 
    return f"""
    <article class="card" itemscope itemtype="https://schema.org/Event"  data-city="{e['city']}">
      <div class="card-header" style="display:flex; align-items:flex-start; gap:1em;">
        <img class="logo-img" alt="Логотип «{e['title']}»" 
             src="img/{e['icon']}" width="72" height="72" 
             style="border-radius:50%; object-fit:cover;">
        <div class="event-info">
          <h2 class="card-title" itemprop="name" style="margin:0 0 .25em 0;">{e['title']}</h2>
          <div class="meta-item">
            <span class="icon">📅</span>
            <time itemprop="startDate" datetime="{e['date']}">{date_str}</time>
          </div>
          <div class="meta-item">
            <span class="icon">📍</span>
            <span itemprop="location" itemscope itemtype="https://schema.org/Place">
              <span itemprop="addressLocality">{address_str}</span>
            </span>
          </div>
        </div>
      </div>
      <p>{e['description']}</p>
      <a href="{registration_url_with_utm}" role="button" target="_blank">Регистрация</a>
      <a href="calendar/{ics_filename}" role="button" download="{ics_filename}" style="margin-left:0.5rem;">Добавить в календарь</a>
    </article>
    """

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
public_calendars = generate_public_calendars(all_events, calendar_dir)

# Генерируем HTML
events_html = "\n".join(render_event(e) for e in events)
public_calendars_html = render_public_calendars(public_calendars)

# Подставляем в шаблон
today_date_str = format_date(date.today(), format="d MMMM y", locale="ru")
result_html = (
    template
    .replace("{{ events }}", events_html)
    .replace("{{ public_calendars }}", public_calendars_html)
    .replace("{{ builddate }}", today_date_str)
)

# Сохраняем результат
OUTPUT_FILE.write_text(result_html, encoding="utf-8")