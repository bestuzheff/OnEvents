"""
Модуль генерации ICS календарей.
Содержит функции для создания VEVENT событий и полного ICS календаря.
"""
# Импорт стандартных модулей
from datetime import datetime
from dateutil.relativedelta import relativedelta
from babel.dates import format_date

# Импорт собственных утилит
from utils.text import clean_text, to_hhmmss
from url_utils import get_timezone_for_event, shorten_url, map_link


def generate_event_vevent(event: dict, session: dict | None = None, session_index: int | None = None) -> str:
    """Генерирует VEVENT (событие календаря) в текстовом формате iCalendar.

    Args:
        event: Словарь с данными события (title, date, city, address, description и т.д.).
        session: Словарь с данными сессии (date, start_time, end_time), если есть.
        session_index: Индекс сессии (1, 2, ...), если событие многосессионное.

    Returns:
        Строка с текстовым представлением VEVENT для ICS файла.

    Особенности:
        - Для многосессионных событий создает отдельный VEVENT на каждую сессию
        - Использует UID из YAML файла (поле 'id'), дефисы удаляются
        - Для сессий к UID добавляется индекс сессии
        - Добавляет ссылку на Яндекс.Карты если есть адрес
    """
    # Используем ID из YAML файла, убираем дефисы для совместимости
    base_uid = event.get('id', '').replace('-', '')

    # Для сессий добавляем индекс, чтобы сделать UID уникальным
    if session_index is not None:
        uid = f"{base_uid}ses{session_index}"
    else:
        uid = base_uid

    # Формируем местоположение (город + адрес)
    location = event.get('city', '')
    if not location:
        location = "Online"

    address = event.get('address')
    if address:
        location += f", {address}"

    # Очищаем текст для ICS (экранируем спецсимволы)
    title = clean_text(event['title'])
    description = clean_text(event['description'])

    # Определяем временную зону для события
    tzid = get_timezone_for_event(event)
    tz_param = f";TZID={tzid}" if tzid else ""

    # Выбираем тип генерации: для сессии или простого события
    if session:
        return _generate_session_vevent(
            event, session, uid, location, title, description,
            tz_param, tzid
        )
    else:
        return _generate_simple_vevent(
            event, uid, location, title, description
        )


def _generate_session_vevent(event, session, uid, location, title, description, tz_param, tzid) -> str:
    """Генерирует VEVENT для сессии события (с конкретным временем).

    Args:
        event: Словарь с данными события.
        session: Словарь с данными сессии (date, start_time, end_time).
        uid: Уникальный идентификатор события.
        location: Местоположение (город + адрес).
        title: Название события.
        description: Описание события.
        tz_param: Параметр временной зоны для DTSTART/DTEND.
        tzid: Идентификатор временной зоны.

    Returns:
        Текстовое представление VEVENT.
    """
    # Парсим дату сессии из строки
    session_date = datetime.strptime(session['date'], "%Y-%m-%d")

    # Формируем время начала и окончания в формате ICS (YYYYMMDDTHHMMSS)
    start_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['start_time'])}"
    end_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['end_time'])}"

    # Формируем название сессии с датой (например: "Конференция (15 мая)")
    date_str = format_date(session_date, format="d MMMM", locale="ru")
    session_title = f"{title} ({date_str})"

    # Добавляем ссылку на карту через сервис сокращения ссылок
    map_url = shorten_url(map_link(event.get('city', ''), event.get('address', '')))
    map_text = f"\\n\\nПоказать на карте: {map_url}" if map_url else ""

    # Формируем полное описание события со ссылкой и временем
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


def _generate_simple_vevent(event, uid, location, title, description) -> str:
    """Генерирует VEVENT для простого однодневного события (на весь день).

    Args:
        event: Словарь с данными события.
        uid: Уникальный идентификатор события.
        location: Местоположение (город + адрес).
        title: Название события.
        description: Описание события.

    Returns:
        Текстовое представление VEVENT.
    """
    # Парсим дату события
    event_date = datetime.strptime(event['date'], "%Y-%m-%d")
  
    # Добавляем ссылку на карту
    map_url = shorten_url(map_link(event['city'], event.get('address', '')))
    map_text = f"\\n\\nПоказать на карте: {map_url}" if map_url else ""

    # Формируем описание события
    registration_link = event.get('registration_url') or event.get('url', '')
    description_text = f"{description}\\n\\nСсылка: {registration_link}{map_text}"

    return f"""BEGIN:VEVENT
 UID:{uid}@onevents.ru
 DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}
 SUMMARY:{title}
 DESCRIPTION:{description_text}
 LOCATION:{location}
 STATUS:CONFIRMED
 TRANSP:OPAQUE
 END:VEVENT"""


def generate_public_calendar(
    events: list[dict],
    calendar_name: str | None = None,
    wr_url: str | None = None
) -> str:
    """Генерирует полный ICS календарь со всеми событиями.

    Args:
        events: Список событий для включения в календарь.
        calendar_name: Название календаря (заголовок X-WR-CALNAME).
        wr_url: URL календаря (для X-WR-URL).

    Returns:
        Полный текст ICS файла календаря.
    """
    # Текущее время для метаданных календаря
    now = datetime.now()
    now_str = now.strftime('%Y%m%dT%H%M%SZ')

    # Название календаря по умолчанию
    default_name = "Cобытия 1C - OnEvents"
    cal_name = calendar_name or default_name
    cal_url = wr_url

    # Шапка календаря с метаданными
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
        # Проверяем есть ли сессии у события
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

    # Закрываем календарь
    ics_content += """
END:VCALENDAR"""

    return ics_content


def generate_ics_content(event: dict) -> str:
    """Генерирует ICS файл для одного события.

    Args:
        event: Словарь с данными события.

    Returns:
        Текст ICS файла для скачивания.
    """
    # Начало ICS файла
    ics_content = """BEGIN:VCALENDAR
 VERSION:2.0
 PRODID:-//OnEvents//OnEvents Calendar//RU
 CALSCALE:GREGORIAN
 METHOD:PUBLISH"""

    # Добавляем временную зону если определена
    tzid = get_timezone_for_event(event)
    if tzid:
        ics_content += f"""
X-WR-TIMEZONE:{tzid}"""

    # Добавляем событие или сессии
    if 'sessions' in event and event['sessions']:
        sessions = event['sessions']
        sessions.sort(key=lambda x: x['date'])

        for i, session in enumerate(sessions):
            vevent = generate_event_vevent(event, session, i + 1)
            ics_content += f"\n{vevent}"
    else:
        vevent = generate_event_vevent(event)
        ics_content += f"\n{vevent}"

    # Закрываем ICS файл
    ics_content += """
END:VCALENDAR"""

    return ics_content