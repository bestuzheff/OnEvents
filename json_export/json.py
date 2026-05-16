"""
Экспорт событий и вебинаров в формате JSON.
Используется для импорта данных на сторонние ресурсы.
"""

import json
from pathlib import Path


def serialize_event(event: dict) -> dict:
    """Сериализует событие для JSON, убирая служебные поля.

    Args:
        event: Словарь с данными события из YAML.

    Returns:
        Очищенный словарь для JSON экспорта.

    Убираемые поля:
        - filename (служебное поле для генерации ID)

    Преобразуемые поля:
        - icon: добавляется путь "img/events/" перед именем файла

    Note:
        Поля url и registration_url включаются только если они существуют.
    """
    icon_filename = event.get('icon', '')
    icon_path = f'img/events/{icon_filename}' if icon_filename else ''

    result = {
        'id': event.get('id'),
        'title': event.get('title'),
        'date': event.get('date'),
        'city': event.get('city'),
        'address': event.get('address'),
        'icon': icon_path,
        'description': event.get('description'),
    }

    # Добавляем registration_url только если есть
    registration_url = event.get('registration_url')
    if registration_url:
        result['registration_url'] = registration_url

    # Добавляем url только если есть
    url = event.get('url')
    if url:
        result['url'] = url

    # Добавляем sessions только если есть
    if event.get('sessions'):
        result['sessions'] = event['sessions']

    return result


def serialize_webinar(webinar: dict) -> dict:
    """Сериализует вебинар для JSON экспорта.

    Args:
        webinar: Словарь с данными вебинара.

    Returns:
        Очищенный словарь для JSON экспорта.

    Преобразуемые поля:
        - pic: добавляется путь "img/webinars/" перед именем файла

    Note:
        Поля url и sessions включаются только если существуют.
    """
    pic_filename = webinar.get('pic', '')
    pic_path = f'img/webinars/{pic_filename}' if pic_filename else ''

    result = {
        'id': webinar.get('id'),
        'title': webinar.get('title'),
        'date': webinar.get('date'),
        'pic': pic_path,
        'description': webinar.get('description'),
    }

    url = webinar.get('url')
    if url:
        result['url'] = url

    sessions = webinar.get('sessions')
    if sessions:
        result['sessions'] = sessions

    return result


def export_to_json(
    items: list[dict],
    output_dir: Path,
    filename: str,
    serializer,
) -> Path:
    """Экспортирует список объектов в JSON файл.

    Args:
        items: Список объектов для экспорта.
        output_dir: Директория для сохранения файла.
        filename: Имя выходного JSON файла.
        serializer: Функция сериализации объекта.

    Returns:
        Путь к созданному JSON файлу.
    """
    data = [serializer(item) for item in items]

    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return output_path


def export_events_to_json(
    all_events: list[dict],
    output_dir: Path,
) -> Path:
    """Экспортирует все события в JSON файл."""
    return export_to_json(
        items=all_events,
        output_dir=output_dir,
        filename='events.json',
        serializer=serialize_event,
    )


def export_upcoming_events_to_json(
    events: list[dict],
    output_dir: Path,
) -> Path:
    """Экспортирует предстоящие события в JSON файл."""
    return export_to_json(
        items=events,
        output_dir=output_dir,
        filename='events_upcoming.json',
        serializer=serialize_event,
    )


def export_webinars_to_json(
    all_webinars: list[dict],
    output_dir: Path,
) -> Path:
    """Экспортирует все вебинары в JSON файл."""
    return export_to_json(
        items=all_webinars,
        output_dir=output_dir,
        filename='webinars.json',
        serializer=serialize_webinar,
    )


def export_upcoming_webinars_to_json(
    webinars: list[dict],
    output_dir: Path,
) -> Path:
    """Экспортирует предстоящие вебинары в JSON файл."""
    return export_to_json(
        items=webinars,
        output_dir=output_dir,
        filename='webinars_upcoming.json',
        serializer=serialize_webinar,
    )
