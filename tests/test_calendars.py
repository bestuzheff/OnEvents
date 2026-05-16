from unittest.mock import patch

from ics_calendars.vevents import (
    generate_event_vevent,
    generate_ics_content,
    generate_public_calendar,
)


class TestICSCalendars:
    @patch('ics_calendars.vevents.uuid.uuid4')
    @patch('ics_calendars.vevents.shorten_url')
    @patch('ics_calendars.vevents.map_link')
    @patch('ics_calendars.vevents.get_timezone_for_event')
    def test_generate_simple_event_vevent(
        self,
        mock_timezone,
        mock_map_link,
        mock_shorten_url,
        mock_uuid,
    ):
        mock_uuid.return_value = 'test-uuid'
        mock_timezone.return_value = 'Europe/Moscow'
        mock_map_link.return_value = 'https://maps.example'
        mock_shorten_url.return_value = 'https://short.url'

        event = {
            'title': 'Конференция',
            'description': 'Описание',
            'date': '2026-05-11',
            'city': 'Москва',
            'address': 'Красная площадь',
            'url': 'https://example.com',
        }

        result = generate_event_vevent(event)

        assert 'BEGIN:VEVENT' in result
        assert 'SUMMARY:Конференция' in result
        assert 'LOCATION:Москва, Красная площадь' in result
        assert 'UID:test-uuid@onevents.ru' in result
        assert 'DTSTART;VALUE=DATE:20260511' in result

    @patch('ics_calendars.vevents.uuid.uuid4')
    @patch('ics_calendars.vevents.shorten_url')
    @patch('ics_calendars.vevents.map_link')
    @patch('ics_calendars.vevents.get_timezone_for_event')
    def test_generate_session_vevent(
        self,
        mock_timezone,
        mock_map_link,
        mock_shorten_url,
        mock_uuid,
    ):
        mock_uuid.return_value = 'test-uuid'
        mock_timezone.return_value = 'Europe/Moscow'
        mock_map_link.return_value = 'https://maps.example'
        mock_shorten_url.return_value = 'https://short.url'

        event = {
            'title': 'Конференция',
            'description': 'Описание',
            'city': 'Москва',
            'address': 'Красная площадь',
            'url': 'https://example.com',
        }

        session = {
            'date': '2026-05-11',
            'start_time': '10:00',
            'end_time': '18:00',
        }

        result = generate_event_vevent(event, session)

        assert 'BEGIN:VEVENT' in result
        assert 'DTSTART;TZID=Europe/Moscow:20260511T100000' in result
        assert 'DTEND;TZID=Europe/Moscow:20260511T180000' in result
        assert 'SUMMARY:Конференция' in result

    @patch('ics_calendars.vevents.generate_event_vevent')
    def test_generate_public_calendar(self, mock_generate_event):
        mock_generate_event.return_value = 'VEVENT_CONTENT'

        events = [{'title': 'Событие', 'date': '2026-05-11'}]

        result = generate_public_calendar(events)

        assert 'BEGIN:VCALENDAR' in result
        assert 'END:VCALENDAR' in result
        assert 'VEVENT_CONTENT' in result

    @patch('ics_calendars.vevents.generate_event_vevent')
    @patch('ics_calendars.vevents.get_timezone_for_event')
    def test_generate_ics_content(
        self,
        mock_timezone,
        mock_generate_event,
    ):
        mock_timezone.return_value = 'Europe/Moscow'
        mock_generate_event.return_value = 'VEVENT_CONTENT'

        event = {'title': 'Событие', 'date': '2026-05-11'}

        result = generate_ics_content(event)

        assert 'BEGIN:VCALENDAR' in result
        assert 'X-WR-TIMEZONE:Europe/Moscow' in result
        assert 'VEVENT_CONTENT' in result
        assert 'END:VCALENDAR' in result
