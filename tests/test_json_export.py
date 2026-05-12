import unittest
from pathlib import Path
from unittest.mock import mock_open, patch

from json_export.json import (
    export_events_to_json,
    export_to_json,
    export_upcoming_events_to_json,
    export_upcoming_webinars_to_json,
    export_webinars_to_json,
    serialize_event,
    serialize_webinar,
)


class TestJsonExport(unittest.TestCase):
    def setUp(self):
        self.event = {
            'id': 'event-1',
            'title': 'Conference',
            'date': '2026-05-01',
            'city': 'Moscow',
            'address': 'Red Square',
            'icon': 'event.png',
            'description': 'Event description',
            'registration_url': 'https://register.example.com',
            'url': 'https://event.example.com',
            'sessions': [{'title': 'Session 1'}],
        }

        self.webinar = {
            'id': 'webinar-1',
            'title': 'Python Webinar',
            'date': '2026-05-10',
            'pic': 'webinar.png',
            'description': 'Webinar description',
            'url': 'https://webinar.example.com',
            'sessions': [{'title': 'Intro'}],
        }

        self.output_dir = Path('/tmp')

    def test_serialize_event(self):
        result = serialize_event(self.event)

        self.assertEqual(result['id'], 'event-1')
        self.assertEqual(result['title'], 'Conference')
        self.assertEqual(result['icon'], 'img/events/event.png')
        self.assertEqual(
            result['registration_url'],
            'https://register.example.com',
        )
        self.assertEqual(
            result['url'],
            'https://event.example.com',
        )
        self.assertEqual(result['sessions'], [{'title': 'Session 1'}])

    def test_serialize_event_without_optional_fields(self):
        event = {
            'id': 'event-2',
            'title': 'Simple Event',
            'date': '2026-05-01',
            'description': 'Description',
        }

        result = serialize_event(event)

        self.assertNotIn('registration_url', result)
        self.assertNotIn('url', result)
        self.assertNotIn('sessions', result)
        self.assertEqual(result['icon'], '')

    def test_serialize_webinar(self):
        result = serialize_webinar(self.webinar)

        self.assertEqual(result['id'], 'webinar-1')
        self.assertEqual(result['title'], 'Python Webinar')
        self.assertEqual(result['pic'], 'img/webinars/webinar.png')
        self.assertEqual(
            result['url'],
            'https://webinar.example.com',
        )
        self.assertEqual(result['sessions'], [{'title': 'Intro'}])

    def test_serialize_webinar_without_optional_fields(self):
        webinar = {
            'id': 'webinar-2',
            'title': 'Simple Webinar',
            'date': '2026-05-11',
            'description': 'Description',
        }

        result = serialize_webinar(webinar)

        self.assertNotIn('url', result)
        self.assertNotIn('sessions', result)
        self.assertEqual(result['pic'], '')

    @patch('json_export.json.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_export_to_json(
        self,
        mock_file,
        mock_json_dump,
    ):
        items = [self.event]

        result = export_to_json(
            items=items,
            output_dir=self.output_dir,
            filename='events.json',
            serializer=serialize_event,
        )

        expected_path = self.output_dir / 'events.json'

        self.assertEqual(result, expected_path)

        mock_file.assert_called_once_with(
            expected_path,
            'w',
            encoding='utf-8',
        )

        mock_json_dump.assert_called_once()

        dumped_data = mock_json_dump.call_args[0][0]

        self.assertEqual(dumped_data[0]['id'], 'event-1')
        self.assertEqual(
            dumped_data[0]['icon'],
            'img/events/event.png',
        )

    @patch('json_export.json.export_to_json')
    def test_export_events_to_json(self, mock_export):
        mock_export.return_value = self.output_dir / 'events.json'

        result = export_events_to_json(
            [self.event],
            self.output_dir,
        )

        self.assertEqual(result, self.output_dir / 'events.json')

        mock_export.assert_called_once_with(
            items=[self.event],
            output_dir=self.output_dir,
            filename='events.json',
            serializer=serialize_event,
        )

    @patch('json_export.json.export_to_json')
    def test_export_upcoming_events_to_json(self, mock_export):
        mock_export.return_value = (
            self.output_dir / 'events_upcoming.json'
        )

        result = export_upcoming_events_to_json(
            [self.event],
            self.output_dir,
        )

        self.assertEqual(
            result,
            self.output_dir / 'events_upcoming.json',
        )

        mock_export.assert_called_once_with(
            items=[self.event],
            output_dir=self.output_dir,
            filename='events_upcoming.json',
            serializer=serialize_event,
        )

    @patch('json_export.json.export_to_json')
    def test_export_webinars_to_json(self, mock_export):
        mock_export.return_value = self.output_dir / 'webinars.json'

        result = export_webinars_to_json(
            [self.webinar],
            self.output_dir,
        )

        self.assertEqual(result, self.output_dir / 'webinars.json')

        mock_export.assert_called_once_with(
            items=[self.webinar],
            output_dir=self.output_dir,
            filename='webinars.json',
            serializer=serialize_webinar,
        )

    @patch('json_export.json.export_to_json')
    def test_export_upcoming_webinars_to_json(self, mock_export):
        mock_export.return_value = (
            self.output_dir / 'webinars_upcoming.json'
        )

        result = export_upcoming_webinars_to_json(
            [self.webinar],
            self.output_dir,
        )

        self.assertEqual(
            result,
            self.output_dir / 'webinars_upcoming.json',
        )

        mock_export.assert_called_once_with(
            items=[self.webinar],
            output_dir=self.output_dir,
            filename='webinars_upcoming.json',
            serializer=serialize_webinar,
        )
