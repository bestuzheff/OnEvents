"""
Генераторы публичных календарей.
Создают ICS файлы для скачивания и подписки.
"""

from pathlib import Path

from ics_calendars.vevents import (
    generate_ics_content,
    generate_public_calendar,
)
from utils.text import DASHES_SPACES_PATTERN, SAFE_CHARS_PATTERN, make_slug


def generate_public_calendars(
    all_events: list[dict], calendar_dir: Path
) -> list[tuple[str, str, str]]:
    """Генерирует публичные календари (общий и по городам).

    Args:
        all_events: Список всех событий.
        calendar_dir: Директория для сохранения файлов.

    Returns:
        Список кортежей (название_города, URL_календаря, город).
        Используется для создания HTML блока с ссылками на календари.

    Генерируемые файлы:
        - onevents-public.ics - общий календарь со всеми событиями
        - onevents-public-{city}.ics - календарь для конкретного города

    Примеры URL:
        - https://onevents.ru/calendar/onevents-public.ics
        - https://onevents.ru/calendar/onevents-public-moskva.ics
    """
    public_calendars = []

    # Создаем общий календарь со всеми событиями
    public_calendar_url = 'https://onevents.ru/calendar/onevents-public.ics'
    public_calendar_content = generate_public_calendar(
        all_events,
        calendar_name='События 1С - OnEvents',
        wr_url=public_calendar_url,
    )
    public_calendar_path = calendar_dir / 'onevents-public.ics'
    public_calendar_path.write_text(public_calendar_content, encoding='utf-8')

    # Добавляем общий календарь в список (для всех городов)
    public_calendars.append(('Все города', public_calendar_url, ''))

    # Создаем отдельные календари по городам
    unique_cities = sorted(
        {e.get('city', '').strip() for e in all_events if e.get('city')}
    )
    for city in unique_cities:
        # Фильтруем события города
        city_events = [e for e in all_events if e.get('city') == city]

        # Создаем слаг для имени файла
        city_slug = make_slug(city)
        city_filename = f'onevents-public-{city_slug}.ics'
        city_url = f'https://onevents.ru/calendar/{city_filename}'
        city_calendar_name = f'События 1С. {city} - OnEvents'

        # Генерируем календарь для города
        city_calendar_content = generate_public_calendar(
            city_events,
            calendar_name=city_calendar_name,
            wr_url=city_url,
        )
        (calendar_dir / city_filename).write_text(
            city_calendar_content, encoding='utf-8'
        )

        # Добавляем в список
        public_calendars.append((city, city_url, city))

    return public_calendars


def generate_webinars_public_calendar(
    all_webinars: list[dict], calendar_dir: Path
) -> str:
    """Генерирует отдельный публичный календарь для вебинаров.

    Args:
        all_webinars: Список всех вебинаров.
        calendar_dir: Директория для сохранения файла.

    Returns:
        URL созданного календаря.

    Note:
        Вебинары хранятся в отдельном календаре, так как они не привязаны к городам.
    """
    webinars_calendar_url = 'https://onevents.ru/calendar/onevents-webinars.ics'
    webinars_calendar_content = generate_public_calendar(
        all_webinars,
        calendar_name='Прямой эфир — OnEvents',
        wr_url=webinars_calendar_url,
    )
    webinars_calendar_path = calendar_dir / 'onevents-webinars.ics'
    webinars_calendar_path.write_text(webinars_calendar_content, encoding='utf-8')

    return webinars_calendar_url


def generate_event_calendars(events: list[dict], calendar_dir: Path) -> None:
    """Генерирует индивидуальные ICS файлы для каждого события.

    Args:
        events: Список событий (или вебинаров).
        calendar_dir: Директория для сохранения файлов.

    Note:
        Каждый вызов функции создает отдельный .ics файл для каждого события.
        Имя файла формируется как: {дата}-{safe_title}.ics

    Примеры имен файлов:
        - 2025-09-15-moskovskaya-konferentsiya.ics
        - 2025-09-16-vebinar-1s.ics
    """
    for event in events:
        # Генерируем безопасное имя файла из названия
        safe_title = SAFE_CHARS_PATTERN.sub('', event['title']).strip()
        safe_title = DASHES_SPACES_PATTERN.sub('-', safe_title)
        ics_filename = f'{event["date"]}-{safe_title}.ics'

        # Генерируем содержимое
        ics_content = generate_ics_content(event)

        # Сохраняем файл
        ics_file_path = calendar_dir / ics_filename
        ics_file_path.write_text(ics_content, encoding='utf-8')
