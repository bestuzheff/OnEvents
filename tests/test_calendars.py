import unittest
from unittest.mock import patch

from ics_calendars import (
    generate_event_vevent,
    generate_public_calendar,
    generate_ics_content,
)


class TestICSCalendars(unittest.TestCase):
    @patch("ics_calendars.uuid.uuid4")
    @patch("ics_calendars.shorten_url")
    @patch("ics_calendars.map_link")
    @patch("ics_calendars.get_timezone_for_event")
    def test_generate_simple_event_vevent(
        self,
        mock_timezone,
        mock_map_link,
        mock_shorten_url,
        mock_uuid,
    ):
        """Тестирует генерацию простого VEVENT."""
        mock_uuid.return_value = "test-uuid"
        mock_timezone.return_value = "Europe/Moscow"
        mock_map_link.return_value = "https://maps.example"
        mock_shorten_url.return_value = "https://short.url"

        event = {
            "title": "Конференция",
            "description": "Описание",
            "date": "2026-05-11",
            "city": "Москва",
            "address": "Красная площадь",
            "url": "https://example.com",
        }

        result = generate_event_vevent(event)

        self.assertIn("BEGIN:VEVENT", result)
        self.assertIn("SUMMARY:Конференция", result)
        self.assertIn("LOCATION:Москва, Красная площадь", result)
        self.assertIn("UID:test-uuid@onevents.ru", result)
        self.assertIn("DTSTART;VALUE=DATE:20260511", result)

    @patch("ics_calendars.uuid.uuid4")
    @patch("ics_calendars.shorten_url")
    @patch("ics_calendars.map_link")
    @patch("ics_calendars.get_timezone_for_event")
    def test_generate_session_vevent(
        self,
        mock_timezone,
        mock_map_link,
        mock_shorten_url,
        mock_uuid,
    ):
        """Тестирует генерацию VEVENT для сессии."""
        mock_uuid.return_value = "test-uuid"
        mock_timezone.return_value = "Europe/Moscow"
        mock_map_link.return_value = "https://maps.example"
        mock_shorten_url.return_value = "https://short.url"

        event = {
            "title": "Конференция",
            "description": "Описание",
            "city": "Москва",
            "address": "Красная площадь",
            "url": "https://example.com",
        }

        session = {
            "date": "2026-05-11",
            "start_time": "10:00",
            "end_time": "18:00",
        }

        result = generate_event_vevent(event, session)

        self.assertIn("BEGIN:VEVENT", result)
        self.assertIn("DTSTART;TZID=Europe/Moscow:20260511T100000", result)
        self.assertIn("DTEND;TZID=Europe/Moscow:20260511T180000", result)
        self.assertIn("SUMMARY:Конференция", result)

    @patch("ics_calendars.generate_event_vevent")
    def test_generate_public_calendar(self, mock_generate_event):
        """Тестирует генерацию полного календаря."""
        mock_generate_event.return_value = "VEVENT_CONTENT"

        events = [
            {
                "title": "Событие",
                "date": "2026-05-11",
            }
        ]

        result = generate_public_calendar(events)

        self.assertIn("BEGIN:VCALENDAR", result)
        self.assertIn("END:VCALENDAR", result)
        self.assertIn("VEVENT_CONTENT", result)

    @patch("ics_calendars.generate_event_vevent")
    @patch("ics_calendars.get_timezone_for_event")
    def test_generate_ics_content(
        self,
        mock_timezone,
        mock_generate_event,
    ):
        """Тестирует генерацию ICS файла."""
        mock_timezone.return_value = "Europe/Moscow"
        mock_generate_event.return_value = "VEVENT_CONTENT"

        event = {
            "title": "Событие",
            "date": "2026-05-11",
        }

        result = generate_ics_content(event)

        self.assertIn("BEGIN:VCALENDAR", result)
        self.assertIn("X-WR-TIMEZONE:Europe/Moscow", result)
        self.assertIn("VEVENT_CONTENT", result)
        self.assertIn("END:VCALENDAR", result)