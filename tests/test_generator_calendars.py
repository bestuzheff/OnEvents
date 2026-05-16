from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ics_calendars.generators import (
    generate_event_calendars,
    generate_public_calendars,
    generate_webinars_public_calendar,
)


class TestCalendarGenerators:
    @patch('ics_calendars.generators.generate_public_calendar')
    def test_generate_public_calendars(self, mock_generate_public_calendar):
        mock_generate_public_calendar.return_value = 'TEST_ICS_CONTENT'

        events = [
            {'title': 'Конференция Москва', 'city': 'Москва', 'date': '2026-05-11'},
            {'title': 'Конференция СПб', 'city': 'Санкт-Петербург', 'date': '2026-05-12'},
        ]

        with TemporaryDirectory() as temp_dir:
            calendar_dir = Path(temp_dir)

            result = generate_public_calendars(events, calendar_dir)

            assert len(result) == 3
            assert (calendar_dir / 'onevents-public.ics').exists()

            city_files = list(calendar_dir.glob('onevents-public-*.ics'))
            assert len(city_files) == 2

            assert mock_generate_public_calendar.call_count == 3

    @patch('ics_calendars.generators.generate_public_calendar')
    def test_generate_webinars_public_calendar(self, mock_generate_public_calendar):
        mock_generate_public_calendar.return_value = 'WEBINAR_ICS'

        webinars = [{'title': 'Вебинар 1', 'date': '2026-05-11'}]

        with TemporaryDirectory() as temp_dir:
            calendar_dir = Path(temp_dir)

            result = generate_webinars_public_calendar(webinars, calendar_dir)

            assert result == 'https://onevents.ru/calendar/onevents-webinars.ics'

            webinars_file = calendar_dir / 'onevents-webinars.ics'
            assert webinars_file.exists()
            assert webinars_file.read_text(encoding='utf-8') == 'WEBINAR_ICS'

    @patch('ics_calendars.generators.generate_ics_content')
    def test_generate_event_calendars(self, mock_generate_ics_content):
        mock_generate_ics_content.return_value = 'EVENT_ICS'

        events = [
            {'title': 'Московская конференция!', 'date': '2026-05-11'},
            {'title': 'Вебинар: 1С и ERP', 'date': '2026-05-12'},
        ]

        with TemporaryDirectory() as temp_dir:
            calendar_dir = Path(temp_dir)

            generate_event_calendars(events, calendar_dir)

            created_files = list(calendar_dir.glob('*.ics'))

            assert len(created_files) == 2

            for file_path in created_files:
                assert file_path.read_text(encoding='utf-8') == 'EVENT_ICS'

            assert mock_generate_ics_content.call_count == 2
