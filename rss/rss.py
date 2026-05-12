"""
Генерация RSS ленты событий.
Создает RSS 2.0 фид для агрегаторов и подкастов.
"""

from datetime import datetime, timezone
from email.utils import format_datetime
from babel.dates import format_date
import pytz
import xml.sax.saxutils as saxutils

from html import generate_event_id
from utils.url import get_timezone_for_event


def generate_rss(all_events: list[dict]) -> str:
    """Генерирует RSS 2.0 ленту со всеми событиями.

    Args:
        all_events: Список всех событий (включая прошедшие).

    Returns:
        Полный XML код RSS ленты.

    Структура канала:
        - Название: "События 1С — OnEvents"
        - Ссылка: https://onevents.ru
        - Описание: "Все события 1С от OnEvents"
        - Язык: ru
        - Items: все события от новых к старым

    Особенности:
        - События сортируются от свежего к прошедшему
        - Каждый item содержит: title, link, guid, pubDate, description
        - Дата публикации устанавливается по дате события
    """
    site_url = 'https://onevents.ru'
    rss_url = f'{site_url}/rss/rss.xml'
    rss_items = []
    now = datetime.now(timezone.utc)

    # Сортируем события от новых к старым (для RSS это важно)
    all_events = sorted(all_events, key=lambda e: e['date'], reverse=True)

    for event in all_events:
        # Определяем временную зону для корректной даты
        tz_name = get_timezone_for_event(event) or 'Europe/Moscow'
        tz = pytz.timezone(tz_name)
        event_date = datetime.strptime(event['date'], '%Y-%m-%d')
        event_date = event_date.replace(tzinfo=tz)
        pub_date = format_datetime(event_date)

        # Генерируем ID и ссылку на событие
        event_id = generate_event_id(event, 'event')
        event_link = f'{site_url}/#{event_id}'

        # Экранируем HTML в заголовке
        title = saxutils.escape(event['title'])

        # Формируем описание события
        description_text = (
            f'{event["description"]}\n\n'
            f'Дата: {format_date(event_date.date(), format="d MMMM y", locale="ru")}\n'
            f'Место: {event["city"]}'
        )

        # Добавляем ссылку на регистрацию если есть
        if event.get('registration_url'):
            description_text += f'\nРегистрация: {event["registration_url"]}'

        # GUID - уникальный идентификатор (не permalink)
        guid = f'onevents-{event["filename"]}'

        # Добавляем item в список
        rss_items.append(f"""
        <item>
            <title>{title}</title>
            <link>{event_link}</link>
            <guid isPermaLink="false">{guid}</guid>
            <pubDate>{pub_date}</pubDate>
            <description>{saxutils.escape(description_text)}</description>
        </item>
        """)

    # Собираем полный RSS
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
