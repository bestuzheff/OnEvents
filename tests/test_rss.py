from unittest.mock import patch

from rss.rss import generate_rss


class TestRSSGeneration:
    @patch('rss.rss.generate_event_id')
    @patch('rss.rss.get_timezone_for_event')
    def test_generate_rss_single_event(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        mock_get_timezone.return_value = 'Europe/Moscow'
        mock_generate_event_id.return_value = 'event-123'

        events = [
            {
                'title': 'Конференция 1С',
                'description': 'Описание события',
                'date': '2026-05-11',
                'city': 'Москва',
                'filename': 'event.yml',
                'registration_url': 'https://register.com',
            }
        ]

        result = generate_rss(events)

        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        assert '<title>События 1С — OnEvents</title>' in result
        assert '<title>Конференция 1С</title>' in result
        assert 'https://onevents.ru/#event-123' in result
        assert 'Описание события' in result
        assert 'Регистрация: https://register.com' in result
        assert 'onevents-event.yml' in result

    @patch('rss.rss.generate_event_id')
    @patch('rss.rss.get_timezone_for_event')
    def test_generate_rss_without_registration_url(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        mock_get_timezone.return_value = 'Europe/Moscow'
        mock_generate_event_id.return_value = 'event-456'

        events = [
            {
                'title': 'Митап',
                'description': 'Описание',
                'date': '2026-06-01',
                'city': 'СПб',
                'filename': 'meetup.yml',
            }
        ]

        result = generate_rss(events)

        assert '<item>' in result
        assert 'Регистрация:' not in result

    @patch('rss.rss.generate_event_id')
    @patch('rss.rss.get_timezone_for_event')
    def test_generate_rss_escapes_html(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        mock_get_timezone.return_value = 'Europe/Moscow'
        mock_generate_event_id.return_value = 'event-html'

        events = [
            {
                'title': '<b>Конференция</b>',
                'description': 'Описание <test>',
                'date': '2026-07-01',
                'city': 'Москва',
                'filename': 'html.yml',
            }
        ]

        result = generate_rss(events)

        assert '&lt;b&gt;Конференция&lt;/b&gt;' in result
        assert 'Описание &lt;test&gt;' in result

    @patch('rss.rss.generate_event_id')
    @patch('rss.rss.get_timezone_for_event')
    def test_generate_rss_sorting(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        mock_get_timezone.return_value = 'Europe/Moscow'
        mock_generate_event_id.return_value = 'event-id'

        events = [
            {
                'title': 'Старое событие',
                'description': 'Описание',
                'date': '2026-01-01',
                'city': 'Москва',
                'filename': 'old.yml',
            },
            {
                'title': 'Новое событие',
                'description': 'Описание',
                'date': '2026-12-01',
                'city': 'Москва',
                'filename': 'new.yml',
            },
        ]

        result = generate_rss(events)

        assert result.find('Новое событие') < result.find('Старое событие')

    @patch('rss.rss.generate_event_id')
    @patch('rss.rss.get_timezone_for_event')
    def test_generate_rss_default_timezone(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        mock_get_timezone.return_value = None
        mock_generate_event_id.return_value = 'event-timezone'

        events = [
            {
                'title': 'Событие',
                'description': 'Описание',
                'date': '2026-05-11',
                'city': 'Онлайн',
                'filename': 'tz.yml',
            }
        ]

        result = generate_rss(events)

        assert '<pubDate>' in result
        assert '</pubDate>' in result

    def test_generate_empty_rss(self):
        result = generate_rss([])

        assert '<rss version="2.0"' in result
        assert '<channel>' in result
        assert '</channel>' in result
        assert '</rss>' in result
