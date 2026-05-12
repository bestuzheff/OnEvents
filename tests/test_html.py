import unittest
from html.cards import (
    generate_event_id,
    render_event,
    render_webinar,
)
from unittest.mock import patch


class TestHtmlRendering(unittest.TestCase):
    def test_generate_event_id(self):
        """Тестирует генерацию ID события."""
        event = {
            'filename': '2026-05-11_conf',
        }

        result = generate_event_id(event, 'event')

        self.assertEqual(result, 'event-2026-05-11_conf')

    @patch('html.cards.map_link')
    @patch('html.cards.add_utm_marks')
    @patch('html.cards.format_time_until_ru')
    def test_render_event_full(
        self,
        mock_format_time,
        mock_add_utm,
        mock_map_link,
    ):
        """Тестирует полный рендер события."""
        mock_format_time.return_value = 'через 10 дней'
        mock_add_utm.return_value = 'https://register.com?utm=test'
        mock_map_link.return_value = 'https://maps.yandex.ru/test'

        event = {
            'title': 'Конференция 1С',
            'date': '2026-05-11',
            'city': 'Москва',
            'address': 'Красная площадь',
            'icon': 'logo.png',
            'description': 'Описание события',
            'registration_url': 'https://register.com',
            'filename': 'conf.yml',
        }

        result = render_event(event)

        self.assertIn('Конференция 1С', result)

        self.assertIn('Описание события', result)

        self.assertIn('через 10 дней', result)

        self.assertIn('https://register.com?utm=test', result)

        self.assertIn('Показать на карте', result)

        self.assertIn('calendar/2026-05-11-Конференция-1С.ics', result)

        self.assertIn('data-city="Москва"', result)

        self.assertIn('id="event-conf.yml"', result)

    @patch('html.cards.map_link')
    @patch('html.cards.add_utm_marks')
    @patch('html.cards.format_time_until_ru')
    def test_render_event_without_optional_fields(
        self,
        mock_format_time,
        mock_add_utm,
        mock_map_link,
    ):
        """Тестирует рендер события без optional полей."""
        mock_format_time.return_value = 'сегодня'
        mock_add_utm.return_value = ''
        mock_map_link.return_value = ''

        event = {
            'title': 'Митап',
            'date': '2026-06-01',
            'city': 'СПб',
            'icon': 'meetup.png',
            'description': 'Описание',
            'filename': 'meetup.yml',
        }

        result = render_event(event)

        self.assertIn('Митап', result)

        self.assertIn('сегодня', result)

        # Нет кнопки регистрации
        self.assertNotIn('Регистрация', result)

        # Нет ссылки карты
        self.assertNotIn('Показать на карте', result)

    def test_render_webinar(self):
        """Тестирует рендер вебинара."""
        webinar = {
            'title': 'Вебинар по ERP',
            'date': '2026-07-01',
            'pic': 'erp.png',
            'description': 'Описание вебинара',
            'url': 'https://youtube.com/test',
            'filename': 'webinar.yml',
        }

        result = render_webinar(webinar)

        self.assertIn('Вебинар по ERP', result)

        self.assertIn('Описание вебинара', result)

        self.assertIn('https://youtube.com/test', result)

        self.assertIn('Трансляция', result)

        self.assertIn('calendar/2026-07-01-Вебинар-по-ERP.ics', result)

        self.assertIn('id="webinar-webinar.yml"', result)

    def test_render_webinar_contains_image(self):
        """Тестирует наличие картинки вебинара."""
        webinar = {
            'title': 'Тест',
            'date': '2026-07-01',
            'pic': 'test.png',
            'description': 'Описание',
            'url': 'https://example.com',
            'filename': 'test.yml',
        }

        result = render_webinar(webinar)

        self.assertIn('src="img/webinars/test.png"', result)

    @patch('html.cards.map_link')
    @patch('html.cards.add_utm_marks')
    @patch('html.cards.format_time_until_ru')
    def test_render_event_without_address(
        self,
        mock_format_time,
        mock_add_utm,
        mock_map_link,
    ):
        """Тестирует событие без адреса."""
        mock_format_time.return_value = 'завтра'
        mock_add_utm.return_value = ''
        mock_map_link.return_value = ''

        event = {
            'title': 'Онлайн митап',
            'date': '2026-08-01',
            'city': 'Онлайн',
            'icon': 'online.png',
            'description': 'Описание',
            'filename': 'online.yml',
        }

        result = render_event(event)

        self.assertIn('Онлайн', result)

        self.assertNotIn('Онлайн, ', result)
