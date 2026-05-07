"""
Модуль генерации ICS календарей.
Содержит функции для создания VEVENT событий и полного ICS календаря.
"""
from datetime import datetime
from babel.dates import format_date

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
        - Использует UID из YAML файла (поле 'id'), для сессий добавляется индекс
        - Добавляет ссылку на Яндекс.Карты если есть адрес
    """
    # Используем ID из YAML файла события
    base_uid = event.get('id', '')

    # Для сессий добавляем индекс, чтобы сделать UID уникальным
    if session_index is not None:
        uid = f"{base_uid}-session-{session_index}"
    else:
        uid = base_uid

    # Формируем местоположение (город + адрес)
    location = event.get('city', '')
    if not location:
        location = "Online"

    address = event.get('address')
    if address:
        location += f", {address}"

    # Очищаем текст для ICS
    title = clean_text(event['title'])
    description = clean_text(event['description'])

    # Определяем временную зону
    tzid = get_timezone_for_event(event)
    tz_param = f";TZID={tzid}" if tzid else ""

    # Генерируем VEVENT для сессии или обычного события
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
    """Генерирует VEVENT для сессии события."""
    session_date = datetime.strptime(session['date'], "%Y-%m-%d")

    # Формируем время начала и окончания
    start_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['start_time'])}"
    end_datetime = f"{session_date.strftime('%Y%m%d')}T{to_hhmmss(session['end_time'])}"

    # Название сессии с датой
    date_str = format_date(session_date, format="d MMMM", locale="ru")
    session_title = f"{title} ({date_str})"

    # Добавляем ссылку на карту
    map_url = shorten_url(map_link(event.get('city', ''), event.get('address', '')))
    map_text = f"\\n\\nПоказать на карте: {map_url}" if map_url else ""

    # Формируем описание
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
    """Генерирует VEVENT для простого однодневного события."""
    event_date = datetime.strptime(event['date'], "%Y-%m-%d")

    # Добавляем ссылку на карту
    map_url = shorten_url(map_link(event['city'], event.get('address', '')))
    map_text = f"\\n\\nПоказать на карте: {map_url}" if map_url else ""

    # Формируем описание
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

    Особенности:
        - Автоматически обрабатывает многосессионные события
        - Сортирует сессии по дате
        - Добавляет метаданные (версия, продукт, временная зона)
    """
    now = datetime.now()
    now_str = now.strftime('%Y%m%dT%H%M%SZ')

    default_name = "Cобытия 1C - OnEvents"
    cal_name = calendar_name or default_name
    cal_url = wr_url

    # Шапка календаря
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

    # Добавляем все события
    for event in events:
        if 'sessions' in event and event['sessions']:
            # Многосессионное событие - создаем по VEVENT на каждую сессию
            sessions = event['sessions']
            sessions.sort(key=lambda x: x['date'])

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


def generate_ics_content(event: dict) -> str:
    """Генерирует ICS файл для одного события.

    Args:
        event: Словарь с данными события.

    Returns:
        Текст ICS файла для скачивания.

    Note:
        Создает файл для добавления конкретного события в календарь пользователя.
    """
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

    # Добавляем событие (или сессии)
    if 'sessions' in event and event['sessions']:
        sessions = event['sessions']
        sessions.sort(key=lambda x: x['date'])

        for i, session in enumerate(sessions):
            vevent = generate_event_vevent(event, session, i + 1)
            ics_content += f"\n{vevent}"
    else:
        vevent = generate_event_vevent(event)
        ics_content += f"\n{vevent}"

    ics_content += """
END:VCALENDAR"""

    return ics_content