import unittest
from unittest.mock import Mock, patch

from utils.url import (
    add_utm_marks,
    get_timezone_for_event,
    map_link,
    shorten_url,
)


class TestUrlUtils(unittest.TestCase):
    def test_get_timezone_for_event(self):
        """Тестирует определение временной зоны по городу."""
        test_cases = [
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
        ]

        for event_data, expected in test_cases:
            with self.subTest(event_data=event_data):
                self.assertEqual(get_timezone_for_event(event_data), expected)

    def test_shorten_url_empty(self):
        """Тестирует сокращение пустого URL."""
        self.assertEqual(shorten_url(''), '')

    @patch('utils.url.requests.get')
    def test_shorten_url_success(self, mock_get):
        """Тестирует успешное сокращение URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'https://clck.ru/abc123\n'
        mock_get.return_value = mock_response

        result = shorten_url('https://example.com/very-long-url')

        self.assertEqual(result, 'https://clck.ru/abc123')
        mock_get.assert_called_once_with(
            'https://clck.ru/--',
            params={'url': 'https://example.com/very-long-url'},
            timeout=5,
        )

    @patch('utils.url.requests.get')
    def test_shorten_url_non_200(self, mock_get):
        """Тестирует возврат исходного URL при ошибке сервера."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        url = 'https://example.com/test'

        self.assertEqual(shorten_url(url), url)

    @patch('utils.url.requests.get')
    def test_shorten_url_exception(self, mock_get):
        """Тестирует обработку исключений requests."""
        mock_get.side_effect = Exception('Connection error')

        url = 'https://example.com/test'

        self.assertEqual(shorten_url(url), url)

    def test_map_link_success(self):
        """Тестирует создание ссылки на карту."""
        result = map_link('Москва', 'Красная площадь, 1')

        self.assertIn('https://yandex.ru/maps/?text=', result)
        self.assertIn('%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0', result)

    def test_map_link_empty_address(self):
        """Тестирует пустой адрес."""
        self.assertEqual(map_link('Москва', ''), '')

    def test_map_link_online_event(self):
        """Тестирует online события."""
        self.assertEqual(map_link('Online', 'Любой адрес'), '')
        self.assertEqual(map_link('онлайн', 'Любой адрес'), '')

    def test_map_link_uncertain_address(self):
        """Тестирует адреса с неопределенными значениями."""
        uncertain_addresses = [
            'Адрес уточняется',
            'TBD',
            'TODO later',
            'Будет объявлено позже',
            'Нужно уточнить',
        ]

        for address in uncertain_addresses:
            with self.subTest(address=address):
                self.assertEqual(map_link('Москва', address), '')

    def test_add_utm_marks_success(self):
        """Тестирует добавление UTM-меток."""
        url = 'https://example.com/event'

        result = add_utm_marks(url)

        self.assertIn('utm_source=onevents.ru', result)
        self.assertIn('utm_medium=website', result)
        self.assertIn('utm_campaign=news', result)
        self.assertIn('utm_content=link', result)

    def test_add_utm_marks_existing_query_params(self):
        """Тестирует добавление UTM к URL с query params."""
        url = 'https://example.com/event?id=123'

        result = add_utm_marks(url)

        self.assertIn('id=123&', result)
        self.assertIn('utm_source=onevents.ru', result)

    def test_add_utm_marks_existing_utm(self):
        """Тестирует URL с уже существующим utm_source."""
        url = 'https://example.com/?utm_source=test'

        self.assertEqual(add_utm_marks(url), url)

    def test_add_utm_marks_telegram_urls(self):
        """Тестирует исключение Telegram URL."""
        telegram_urls = [
            'https://t.me/channel',
            'https://telegram.org/blog',
        ]

        for url in telegram_urls:
            with self.subTest(url=url):
                self.assertEqual(add_utm_marks(url), url)

    def test_add_utm_marks_empty_url(self):
        """Тестирует пустой URL."""
        self.assertEqual(add_utm_marks(''), '')
