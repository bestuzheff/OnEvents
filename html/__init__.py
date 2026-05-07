"""
Генерация HTML карточек событий и вебинаров.
Содержит функции для рендеринга HTML представления событий.
"""
from datetime import datetime
from babel.dates import format_date
from utils.text import SAFE_CHARS_PATTERN, DASHES_SPACES_PATTERN
from utils.dates import format_time_until_ru
from url_utils import add_utm_marks, map_link
from ics_calendars import generate_ics_content


def generate_event_id(event: dict, event_type: str) -> str:
    """Генерирует уникальный ID для события для использования в якорных ссылках.

    Args:
        event: Словарь с данными события.
        event_type: Тип события ('event' или 'webinar').

    Returns:
        Уникальный ID в формате "{type}-{filename}".
        Например: "event-2025-09-15_moskow" или "webinar-2025-09-20_1c_news"

    Note:
        Использует имя файла (filename) как основу, так как оно уже содержит
        дату и краткое описание события.
    """
    return f"{type}-{event['filename']}"


def render_event(event: dict) -> str:
    """Генерирует HTML карточку события для отображения на сайте.

    Args:
        event: Словарь с данными события.

    Returns:
        HTML код карточки события.

    Особенности:
        - Показывает название, дату, город, адрес
        - Добавляет время до события (сегодня, завтра, через X дней/месяцев)
        - Показывает кнопку регистрации если ссылка есть
        - Добавляет ссылку на Яндекс.Карты если есть адрес
        - Добавляет кнопку для скачивания ICS календаря
    """
    # Форматируем дату
    date_obj = datetime.strptime(event['date'], "%Y-%m-%d")
    today_date = datetime.today().date()
    target_date = date_obj.date()
    date_str = format_date(date_obj, format="d MMMM y", locale="ru")

    # Формируем текст "через сколько"
    days_left_text = format_time_until_ru(today_date, target_date)
    days_left_html = f'<span class="days-left">{days_left_text}</span>'

    # Формируем строку адреса (город + адрес)
    address = event.get('address') or ''
    if not address:
        address_str = event['city']
    else:
        address_str = f"{event['city']}, {address}"

    # Генерируем имя файла для ICS
    safe_title = SAFE_CHARS_PATTERN.sub('', event['title']).strip()
    safe_title = DASHES_SPACES_PATTERN.sub('-', safe_title)
    ics_filename = f"{event['date']}-{safe_title}.ics"

    # Обрабатываем ссылку регистрации (добавляем UTM метки)
    raw_registration_url = (event.get('registration_url') or "").strip()
    registration_url_with_utm = add_utm_marks(raw_registration_url) if raw_registration_url else ""
    registration_button_html = ""
    if registration_url_with_utm:
        registration_button_html = f'<a href="{registration_url_with_utm}" role="button" target="_blank">Регистрация</a>'

    # Генерируем ID события
    event_id = generate_event_id(event, "event")

    # Ссылка на карту
    map_url = map_link(event['city'], event.get('address', ''))
    map_link_html = ""
    if map_url:
        map_link_html = f' <a href="{map_url}" target="_blank" class="map-link" title="Показать на карте">Показать на карте</a>'

    return f"""
    <article class="card" itemscope itemtype="https://schema.org/Event" data-city="{event['city']}" id="{event_id}">
      <div class="card-header">
        <div class="card-header-main">
          <img class="logo-img" alt="Логотип «{event['title']}»"
               src="img/events/{event['icon']}" width="72" height="72"
               style="border-radius:15%; object-fit:cover;">
          <div class="event-info">
            <h2 class="card-title" itemprop="name" style="margin:0 0 .25em 0;">{event['title']}</h2>
            <div class="meta-item">
              <span class="icon">📅</span>
              <time itemprop="startDate" datetime="{event['date']}">{date_str} {days_left_html}</time>
            </div>
            <div class="meta-item">
              <span class="icon">📌</span>
              <span itemprop="location" itemscope itemtype="https://schema.org.Place">
                <span itemprop="addressLocality">{address_str}</span>
              </span>
            </div>{map_link_html}
          </div>
        </div>
        <button class="event-copy-btn" data-event-id="{event_id}" title="Копировать ссылку на событие">🔗</button>
      </div>
      <p>{event['description']}</p>
      <div class="event-actions">
        {registration_button_html}
        <a href="calendar/{ics_filename}" role="button" download="{ics_filename}">Добавить в календарь</a>
      </div>
    </article>
    """


def render_webinar(webinar: dict) -> str:
    """Генерирует HTML карточку вебинара для отображения на сайте.

    Args:
        webinar: Словарь с данными вебинара.

    Returns:
        HTML код карточки вебинара.

    Особенности:
        - Показывает название, дату, описание
        - Показывает ссылку на трансляцию
        - Добавляет кнопку для скачивания ICS календаря
    """
    # Форматируем дату
    date_obj = datetime.strptime(webinar['date'], "%Y-%m-%d")
    date_str = format_date(date_obj, format="d MMMM y", locale="ru")

    # Генерируем имя файла для ICS
    safe_title = SAFE_CHARS_PATTERN.sub('', webinar['title']).strip()
    safe_title = DASHES_SPACES_PATTERN.sub('-', safe_title)
    ics_filename = f"{webinar['date']}-{safe_title}.ics"

    # Ссылка на трансляцию
    translation_url = webinar['url']

    # ID вебинара
    webinar_id = generate_event_id(webinar, "webinar")

    return f"""
    <article class="card" itemscope itemtype="https://schema.org/Event" id="{webinar_id}">
      <div class="card-header">
        <div class="card-header-main">
          <img class="logo-img" alt="Логотип «{webinar['title']}»" src="img/webinars/{webinar['pic']}" width="256">
          <div class="event-info">
            <h2 class="card-title" itemprop="name" style="margin:0 0 .25em 0;">{webinar['title']}</h2>
            <div class="meta-item">
              <span class="icon">📅</span>
              <time itemprop="startDate" datetime="{webinar['date']}">{date_str}</time>
            </div>
            {webinar['description']}
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