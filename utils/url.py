"""
Утилиты для работы с URL.
Содержит функции для сокращения ссылок, создания ссылок на карты, добавления UTM-меток.
"""

import json
import urllib.parse
from pathlib import Path

import requests

URL_CACHE_FILE = Path('data/url_cache.json')


def _load_url_cache() -> dict[str, str]:
    if not URL_CACHE_FILE.exists():
        return {}
    return json.loads(URL_CACHE_FILE.read_text(encoding='utf-8'))


def _save_url_cache(cache: dict[str, str]) -> None:
    URL_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = URL_CACHE_FILE.with_suffix('.tmp')
    temporary_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary_file.replace(URL_CACHE_FILE)


def _is_valid_shortened_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme == 'https' and parsed.netloc == 'clck.ru' and parsed.path not in ('', '/')


def shorten_url(url: str) -> str:
    """Возвращает URL из локального кеша или сокращает его через clck.ru.

    Args:
        url: Исходный длинный URL.

    Returns:
        Сокращенный URL или исходный URL, если сокращение не удалось.

    Note:
        Успешные ответы сохраняются в data/url_cache.json для следующих сборок.
        Использует бесплатный сервис clck.ru для сокращения новых ссылок.
        Таймаут запроса - 5 секунд.
    """
    if not url:
        return url

    cache = _load_url_cache()
    if url in cache:
        return cache[url]

    try:
        response = requests.get('https://clck.ru/--', params={'url': url}, timeout=5)
        if response.status_code == 200:
            shortened_url = response.text.strip()
            if not _is_valid_shortened_url(shortened_url):
                return url
            cache[url] = shortened_url
            _save_url_cache(cache)
            return shortened_url
        return url
    except Exception:
        return url


def get_timezone_for_event(event: dict) -> str | None:
    """Определяет временную зону для события на основе города.

    Args:
        event: Словарь с данными события (должен содержать ключ 'city').

    Returns:
        Название временной зоны (например 'Europe/Moscow') или None, если город не найден.

    Поддерживаемые города:
        - Москва, Санкт-Петербург, Online -> Europe/Moscow
        - Новосибирск -> Asia/Novosibirsk
        - Иркутск -> Asia/Irkutsk
    """
    tz_moscow = 'Europe/Moscow'
    timezones = {
        'online': tz_moscow,
        'онлайн': tz_moscow,
        'санкт-петербург': tz_moscow,
        'москва': tz_moscow,
        'новосибирск': 'Asia/Novosibirsk',
        'иркутск': 'Asia/Irkutsk',
    }

    city = str(event.get('city', '')).strip().lower()
    return timezones.get(city)


def map_link(city: str, address: str = '') -> str:
    """Создает ссылку на Яндекс.Карты с адресом события.

    Args:
        city: Название города.
        address: Адрес события (улица, дом).

    Returns:
        Ссылка на Яндекс.Карты или пустая строка, если ссылку создать нельзя.

    Случаи, когда возвращается пустая строка:
        - Адрес пустой
        - Город - Online/Онлайн
        - Адрес содержит слова неопределенности (уточняется, TBD, TODO и т.д.)
    """
    # Не показываем карту если адрес пустой
    if not address:
        return ''

    # Не показываем для онлайн событий
    if city.lower() in ['online', 'онлайн']:
        return ''

    # Проверяем на слова неопределенности в адресе
    uncertain_words = [
        'уточняется',
        'придумано',
        'объявлено',
        'уточнить',
        'tbd',
        'tba',
        'todo',
    ]
    if any(word in address.lower() for word in uncertain_words):
        return ''

    # Формируем полный адрес
    full_address = f'{city}, {address}'
    # URL-кодируем адрес для безопасной вставки в URL
    encoded_address = urllib.parse.quote(full_address)

    return f'https://yandex.ru/maps/?text={encoded_address}'


def add_utm_marks(url: str) -> str:
    """Добавляет UTM-метки к URL для отслеживания трафика.

    Args:
        url: Исходный URL (обычно ссылка на регистрацию).

    Returns:
        URL с добавленными UTM-параметрами или исходный URL без изменений.

    Добавляемые параметры:
        - utm_source=onevents.ru
        - utm_medium=website
        - utm_campaign=news
        - utm_content=link

    Не обрабатываются:
        - Пустые URL
        - URL уже содержащие utm_source
        - URL Telegram (t.me, telegram.org)
    """
    if not url or 'utm_source=' in url:
        return url

    # Исключаем ссылки Telegram
    exclude_urls = ['t.me', 'telegram.org']
    if any(exclude in url for exclude in exclude_urls):
        return url

    # Парсим URL
    parsed = urllib.parse.urlparse(url)

    # Формируем UTM параметры
    utm_source = 'onevents.ru'
    utm_medium = 'website'
    utm_campaign = 'news'
    utm_content = 'link'

    utm_params = (
        f'utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}&utm_content={utm_content}'
    )

    # Добавляем к существующим параметрам запроса
    new_query = f'{parsed.query}&{utm_params}' if parsed.query else utm_params
    new_parsed = parsed._replace(query=new_query)

    return urllib.parse.urlunparse(new_parsed)
