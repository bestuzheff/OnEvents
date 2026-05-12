"""
Экспорт событий и вебинаров в формате JSON.
Используется для импорта данных на сторонние ресурсы.
"""

from pathlib import Path
import json


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


def export_events_to_json(all_events: list[dict], output_dir: Path) -> Path:
    """Экспортирует все события (включая прошедшие) в JSON файл.

    Args:
        all_events: Список всех событий.
        output_dir: Директория для сохранения файла.

    Returns:
        Путь к созданному файлу.

    Output файл:
        events.json - содержит все события отсортированные по дате
    """
    events_data = [serialize_event(e) for e in all_events]

    output_path = output_dir / 'events.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events_data, f, ensure_ascii=False, indent=2)

    return output_path


def export_upcoming_events_to_json(events: list[dict], output_dir: Path) -> Path:
    """Экспортирует только предстоящие события в JSON файл.

    Args:
        events: Список предстоящих событий.
        output_dir: Директория для сохранения файла.

    Returns:
        Путь к созданному файлу.

    Output файл:
        events_upcoming.json - содержит только будущие события
    """
    events_data = [serialize_event(e) for e in events]

    output_path = output_dir / 'events_upcoming.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events_data, f, ensure_ascii=False, indent=2)

    return output_path


def export_webinars_to_json(all_webinars: list[dict], output_dir: Path) -> Path:
    """Экспортирует все вебинары в JSON файл.

    Args:
        all_webinars: Список всех вебинаров.
        output_dir: Директория для сохранения файла.

    Returns:
        Путь к созданному файлу.

    Output файл:
        webinars.json - содержит все вебинары

    Note:
        Для вебинаров поле 'pic' преобразуется в полный путь 'img/webinars/...'
    """
    webinars_data = []

    for w in all_webinars:
        pic_filename = w.get('pic', '')
        pic_path = f'img/webinars/{pic_filename}' if pic_filename else ''

        item = {
            'id': w.get('id'),
            'title': w.get('title'),
            'date': w.get('date'),
            'pic': pic_path,
            'description': w.get('description'),
        }

        # Добавляем url только если есть
        url = w.get('url')
        if url:
            item['url'] = url

        # Добавляем sessions только если есть
        sessions = w.get('sessions')
        if sessions:
            item['sessions'] = sessions

        webinars_data.append(item)

    output_path = output_dir / 'webinars.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(webinars_data, f, ensure_ascii=False, indent=2)

    return output_path


def export_upcoming_webinars_to_json(webinars: list[dict], output_dir: Path) -> Path:
    """Экспортирует только предстоящие вебинары в JSON файл.

    Args:
        webinars: Список предстоящих вебинаров.
        output_dir: Директория для сохранения файла.

    Returns:
        Путь к созданному файлу.

    Output файл:
        webinars_upcoming.json - содержит только будущие вебинары
    """
    webinars_data = []

    for w in webinars:
        pic_filename = w.get('pic', '')
        pic_path = f'img/webinars/{pic_filename}' if pic_filename else ''

        item = {
            'id': w.get('id'),
            'title': w.get('title'),
            'date': w.get('date'),
            'pic': pic_path,
            'description': w.get('description'),
        }

        url = w.get('url')
        if url:
            item['url'] = url

        sessions = w.get('sessions')
        if sessions:
            item['sessions'] = sessions

        webinars_data.append(item)

    output_path = output_dir / 'webinars_upcoming.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(webinars_data, f, ensure_ascii=False, indent=2)

    return output_path
