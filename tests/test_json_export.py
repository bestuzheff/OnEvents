import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from json_export import (
    serialize_event,
    export_events_to_json,
    export_upcoming_events_to_json,
    export_webinars_to_json,
    export_upcoming_webinars_to_json,
)


class TestJsonExport(unittest.TestCase):
    def test_serialize_event_full(self):
        """Тестирует сериализацию события со всеми полями."""
        event = {
            "id": 1,
            "title": "Конференция",
            "date": "2026-05-11",
            "city": "Москва",
            "address": "Красная площадь",
            "icon": "conf.png",
            "description": "Описание",
            "registration_url": "https://register.com",
            "url": "https://event.com",
            "sessions": [
                {
                    "title": "Доклад",
                }
            ],
            "filename": "internal.yml",
        }

        result = serialize_event(event)

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["title"], "Конференция")
        self.assertEqual(
            result["icon"],
            "img/events/conf.png"
        )

        self.assertIn("registration_url", result)
        self.assertIn("url", result)
        self.assertIn("sessions", result)

        # filename не должен попасть в JSON
        self.assertNotIn("filename", result)

    def test_serialize_event_minimal(self):
        """Тестирует сериализацию минимального события."""
        event = {
            "title": "Минимальное событие",
        }

        result = serialize_event(event)

        self.assertEqual(
            result["title"],
            "Минимальное событие"
        )

        self.assertEqual(result["icon"], "")

        self.assertNotIn("url", result)
        self.assertNotIn("registration_url", result)
        self.assertNotIn("sessions", result)

    def test_export_events_to_json(self):
        """Тестирует экспорт событий в JSON."""
        events = [
            {
                "id": 1,
                "title": "Событие",
                "date": "2026-05-11",
            }
        ]

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            output_path = export_events_to_json(
                events,
                output_dir
            )

            self.assertTrue(output_path.exists())
            self.assertEqual(
                output_path.name,
                "events.json"
            )

            data = json.loads(
                output_path.read_text(encoding="utf-8")
            )

            self.assertEqual(len(data), 1)
            self.assertEqual(
                data[0]["title"],
                "Событие"
            )

    def test_export_upcoming_events_to_json(self):
        """Тестирует экспорт будущих событий."""
        events = [
            {
                "id": 2,
                "title": "Будущее событие",
                "date": "2026-06-01",
            }
        ]

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            output_path = export_upcoming_events_to_json(
                events,
                output_dir
            )

            self.assertTrue(output_path.exists())
            self.assertEqual(
                output_path.name,
                "events_upcoming.json"
            )

    def test_export_webinars_to_json(self):
        """Тестирует экспорт вебинаров."""
        webinars = [
            {
                "id": 1,
                "title": "Вебинар",
                "date": "2026-05-11",
                "pic": "webinar.png",
                "description": "Описание",
                "url": "https://webinar.com",
                "sessions": [
                    {
                        "title": "Сессия",
                    }
                ],
            }
        ]

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            output_path = export_webinars_to_json(
                webinars,
                output_dir
            )

            self.assertTrue(output_path.exists())
            self.assertEqual(
                output_path.name,
                "webinars.json"
            )

            data = json.loads(
                output_path.read_text(encoding="utf-8")
            )

            self.assertEqual(len(data), 1)

            self.assertEqual(
                data[0]["pic"],
                "img/webinars/webinar.png"
            )

            self.assertIn("url", data[0])
            self.assertIn("sessions", data[0])

    def test_export_upcoming_webinars_to_json(self):
        """Тестирует экспорт будущих вебинаров."""
        webinars = [
            {
                "id": 2,
                "title": "Будущий вебинар",
                "date": "2026-06-01",
            }
        ]

        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            output_path = (
                export_upcoming_webinars_to_json(
                    webinars,
                    output_dir
                )
            )

            self.assertTrue(output_path.exists())

            self.assertEqual(
                output_path.name,
                "webinars_upcoming.json"
            )