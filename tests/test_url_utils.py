import json
from unittest.mock import Mock, patch

import pytest

import utils.url
from utils.url import (
    add_utm_marks,
    get_timezone_for_event,
    map_link,
    shorten_url,
)


@pytest.fixture(autouse=True)
def url_cache_file(tmp_path, monkeypatch):
    cache_file = tmp_path / 'url_cache.json'
    cache_file.write_text('{}', encoding='utf-8')
    monkeypatch.setattr(utils.url, 'URL_CACHE_FILE', cache_file, raising=False)
    return cache_file


@pytest.mark.parametrize(
    'event_data,expected',
    [
        ({'city': 'Москва'}, 'Europe/Moscow'),
        ({'city': 'москва'}, 'Europe/Moscow'),
        ({'city': 'Онлайн'}, 'Europe/Moscow'),
        ({'city': 'онлайн'}, 'Europe/Moscow'),
        ({'city': 'Санкт-Петербург'}, 'Europe/Moscow'),
        ({'city': 'новосибирск'}, 'Asia/Novosibirsk'),
        ({'city': 'Иркутск'}, 'Asia/Irkutsk'),
        ({'city': 'Неизвестный город'}, None),
        ({'city': ''}, None),
        ({}, None),
        ({'city': None}, None),
    ],
)
def test_get_timezone_for_event(event_data, expected):
    assert get_timezone_for_event(event_data) == expected


def test_shorten_url_empty():
    assert shorten_url('') == ''


@patch('utils.url.requests.get')
def test_shorten_url_success(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = 'https://clck.ru/abc123\n'
    mock_get.return_value = mock_response

    result = shorten_url('https://example.com/very-long-url')

    assert result == 'https://clck.ru/abc123'
    mock_get.assert_called_once_with(
        'https://clck.ru/--',
        params={'url': 'https://example.com/very-long-url'},
        timeout=5,
    )


@patch('utils.url.requests.get')
def test_shorten_url_returns_cached_url_without_request(mock_get, url_cache_file):
    long_url = 'https://example.com/repeated-address'
    url_cache_file.write_text(json.dumps({long_url: 'https://clck.ru/cached'}), encoding='utf-8')

    assert shorten_url(long_url) == 'https://clck.ru/cached'
    mock_get.assert_not_called()


@patch('utils.url.requests.get')
def test_shorten_url_caches_successful_response(mock_get, url_cache_file):
    long_url = 'https://example.com/new-address'
    mock_response = Mock(status_code=200, text='https://clck.ru/new\n')
    mock_get.return_value = mock_response

    assert shorten_url(long_url) == 'https://clck.ru/new'
    assert json.loads(url_cache_file.read_text(encoding='utf-8')) == {long_url: 'https://clck.ru/new'}


@pytest.mark.parametrize('response_text', ['', 'temporary error', '<html>error</html>', 'https://example.com/not-clck'])
@patch('utils.url.requests.get')
def test_shorten_url_does_not_cache_invalid_success_response(mock_get, response_text, url_cache_file):
    long_url = 'https://example.com/new-address'
    mock_get.return_value = Mock(status_code=200, text=response_text)

    assert shorten_url(long_url) == long_url
    assert json.loads(url_cache_file.read_text(encoding='utf-8')) == {}


@patch('utils.url.requests.get')
def test_shorten_url_non_200(mock_get):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    url = 'https://example.com/test'

    assert shorten_url(url) == url


@patch('utils.url.requests.get')
def test_shorten_url_exception(mock_get):
    mock_get.side_effect = Exception('Connection error')

    url = 'https://example.com/test'

    assert shorten_url(url) == url


def test_map_link_success():
    result = map_link('Москва', 'Красная площадь, 1')

    assert 'https://yandex.ru/maps/?text=' in result
    assert '%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0' in result


def test_map_link_empty_address():
    assert map_link('Москва', '') == ''


def test_map_link_online_event():
    assert map_link('Online', 'Любой адрес') == ''
    assert map_link('онлайн', 'Любой адрес') == ''


@pytest.mark.parametrize(
    'address',
    [
        'Адрес уточняется',
        'TBD',
        'TODO later',
        'Будет объявлено позже',
        'Нужно уточнить',
    ],
)
def test_map_link_uncertain_address(address):
    assert map_link('Москва', address) == ''


def test_add_utm_marks_success():
    result = add_utm_marks('https://example.com/event')

    assert 'utm_source=onevents.ru' in result
    assert 'utm_medium=website' in result
    assert 'utm_campaign=news' in result
    assert 'utm_content=link' in result


def test_add_utm_marks_existing_query_params():
    result = add_utm_marks('https://example.com/event?id=123')

    assert 'id=123&' in result
    assert 'utm_source=onevents.ru' in result


def test_add_utm_marks_existing_utm():
    url = 'https://example.com/?utm_source=test'

    assert add_utm_marks(url) == url


@pytest.mark.parametrize(
    'url',
    [
        'https://t.me/channel',
        'https://telegram.org/blog',
    ],
)
def test_add_utm_marks_telegram_urls(url):
    assert add_utm_marks(url) == url


def test_add_utm_marks_empty_url():
    assert add_utm_marks('') == ''
