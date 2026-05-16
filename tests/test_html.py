from html.cards import (
    generate_event_id,
    render_event,
    render_webinar,
)
from unittest.mock import patch


class TestHtmlRendering:
    def test_generate_event_id(self):
        event = {'filename': '2026-05-11_conf'}

        result = generate_event_id(event, 'event')

        assert result == 'event-2026-05-11_conf'

    @patch('html.cards.map_link')
    @patch('html.cards.add_utm_marks')
    @patch('html.cards.format_time_until_ru')
    def test_render_event_full(
        self,
        mock_format_time,
        mock_add_utm,
        mock_map_link,
    ):
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

        assert 'Конференция 1С' in result
        assert 'Описание события' in result
        assert 'через 10 дней' in result
        assert 'https://register.com?utm=test' in result
        assert 'Показать на карте' in result
        assert 'calendar/2026-05-11-Конференция-1С.ics' in result
        assert 'data-city="Москва"' in result
        assert 'id="event-conf.yml"' in result

    @patch('html.cards.map_link')
    @patch('html.cards.add_utm_marks')
    @patch('html.cards.format_time_until_ru')
    def test_render_event_without_optional_fields(
        self,
        mock_format_time,
        mock_add_utm,
        mock_map_link,
    ):
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

        assert 'Митап' in result
        assert 'сегодня' in result
        assert 'Регистрация' not in result
        assert 'Показать на карте' not in result

    def test_render_webinar(self):
        webinar = {
            'title': 'Вебинар по ERP',
            'date': '2026-07-01',
            'pic': 'erp.png',
            'description': 'Описание вебинара',
            'url': 'https://youtube.com/test',
            'filename': 'webinar.yml',
        }

        result = render_webinar(webinar)

        assert 'Вебинар по ERP' in result
        assert 'Описание вебинара' in result
        assert 'https://youtube.com/test' in result
        assert 'Трансляция' in result
        assert 'calendar/2026-07-01-Вебинар-по-ERP.ics' in result
        assert 'id="webinar-webinar.yml"' in result

    def test_render_webinar_contains_image(self):
        webinar = {
            'title': 'Тест',
            'date': '2026-07-01',
            'pic': 'test.png',
            'description': 'Описание',
            'url': 'https://example.com',
            'filename': 'test.yml',
        }

        result = render_webinar(webinar)

        assert 'src="img/webinars/test.png"' in result

    @patch('html.cards.map_link')
    @patch('html.cards.add_utm_marks')
    @patch('html.cards.format_time_until_ru')
    def test_render_event_without_address(
        self,
        mock_format_time,
        mock_add_utm,
        mock_map_link,
    ):
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

        assert 'Онлайн' in result
        assert 'Онлайн, ' not in result
