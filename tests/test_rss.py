import unittest
from unittest.mock import patch

from rss.rss import generate_rss


class TestRSSGeneration(unittest.TestCase):
    @patch("rss.rss.generate_event_id")
    @patch("rss.rss.get_timezone_for_event")
    def test_generate_rss_single_event(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        """Тестирует генерацию RSS для одного события."""
        mock_get_timezone.return_value = "Europe/Moscow"
        mock_generate_event_id.return_value = "event-123"

        events = [
            {
                "title": "Конференция 1С",
                "description": "Описание события",
                "date": "2026-05-11",
                "city": "Москва",
                "filename": "event.yml",
                "registration_url": "https://register.com",
            }
        ]

        result = generate_rss(events)

        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', result)

        self.assertIn(
            "<title>События 1С — OnEvents</title>",
            result
        )

        self.assertIn(
            "<title>Конференция 1С</title>",
            result
        )

        self.assertIn(
            "https://onevents.ru/#event-123",
            result
        )

        self.assertIn(
            "Описание события",
            result
        )

        self.assertIn(
            "Регистрация: https://register.com",
            result
        )

        self.assertIn(
            "onevents-event.yml",
            result
        )

    @patch("rss.rss.generate_event_id")
    @patch("rss.rss.get_timezone_for_event")
    def test_generate_rss_without_registration_url(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        """Тестирует RSS без registration_url."""
        mock_get_timezone.return_value = "Europe/Moscow"
        mock_generate_event_id.return_value = "event-456"

        events = [
            {
                "title": "Митап",
                "description": "Описание",
                "date": "2026-06-01",
                "city": "СПб",
                "filename": "meetup.yml",
            }
        ]

        result = generate_rss(events)

        self.assertIn("<item>", result)

        self.assertNotIn(
            "Регистрация:",
            result
        )

    @patch("rss.rss.generate_event_id")
    @patch("rss.rss.get_timezone_for_event")
    def test_generate_rss_escapes_html(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        """Тестирует экранирование HTML."""
        mock_get_timezone.return_value = "Europe/Moscow"
        mock_generate_event_id.return_value = "event-html"

        events = [
            {
                "title": "<b>Конференция</b>",
                "description": "Описание <test>",
                "date": "2026-07-01",
                "city": "Москва",
                "filename": "html.yml",
            }
        ]

        result = generate_rss(events)

        self.assertIn(
            "&lt;b&gt;Конференция&lt;/b&gt;",
            result
        )

        self.assertIn(
            "Описание &lt;test&gt;",
            result
        )

    @patch("rss.rss.generate_event_id")
    @patch("rss.rss.get_timezone_for_event")
    def test_generate_rss_sorting(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        """Тестирует сортировку событий по дате."""
        mock_get_timezone.return_value = "Europe/Moscow"
        mock_generate_event_id.return_value = "event-id"

        events = [
            {
                "title": "Старое событие",
                "description": "Описание",
                "date": "2026-01-01",
                "city": "Москва",
                "filename": "old.yml",
            },
            {
                "title": "Новое событие",
                "description": "Описание",
                "date": "2026-12-01",
                "city": "Москва",
                "filename": "new.yml",
            },
        ]

        result = generate_rss(events)

        new_pos = result.find("Новое событие")
        old_pos = result.find("Старое событие")

        self.assertLess(new_pos, old_pos)

    @patch("rss.rss.generate_event_id")
    @patch("rss.rss.get_timezone_for_event")
    def test_generate_rss_default_timezone(
        self,
        mock_get_timezone,
        mock_generate_event_id,
    ):
        """Тестирует fallback timezone."""
        mock_get_timezone.return_value = None
        mock_generate_event_id.return_value = "event-timezone"

        events = [
            {
                "title": "Событие",
                "description": "Описание",
                "date": "2026-05-11",
                "city": "Онлайн",
                "filename": "tz.yml",
            }
        ]

        result = generate_rss(events)

        self.assertIn("<pubDate>", result)
        self.assertIn("</pubDate>", result)

    def test_generate_empty_rss(self):
        """Тестирует генерацию пустой RSS ленты."""
        result = generate_rss([])

        self.assertIn("<rss version=\"2.0\"", result)
        self.assertIn("<channel>", result)
        self.assertIn("</channel>", result)
        self.assertIn("</rss>", result)