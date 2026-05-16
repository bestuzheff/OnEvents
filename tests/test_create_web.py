from datetime import date
from pathlib import Path
from unittest.mock import mock_open, patch

import create_web
from create_web import generate_sitemap


def test_generate_sitemap():
    result = generate_sitemap()

    assert '<?xml version="1.0" encoding="UTF-8"?>' in result
    assert 'https://onevents.ru/' in result
    assert 'https://onevents.ru/rss/rss.xml' in result
    assert date.today().isoformat() in result
    assert '<changefreq>daily</changefreq>' in result


class TestCreateWeb:
    @patch('create_web.render_webinars_calendar')
    @patch('create_web.render_public_calendars')
    @patch('create_web.render_webinar')
    @patch('create_web.render_event')
    @patch('create_web.export_upcoming_webinars_to_json')
    @patch('create_web.export_webinars_to_json')
    @patch('create_web.export_upcoming_events_to_json')
    @patch('create_web.export_events_to_json')
    @patch('create_web.generate_rss')
    @patch('create_web.generate_webinars_public_calendar')
    @patch('create_web.generate_public_calendars')
    @patch('create_web.generate_event_calendars')
    @patch('create_web.shutil.copy')
    @patch('create_web.shutil.copytree')
    @patch('create_web.format_date')
    @patch('create_web.yaml.safe_load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.glob')
    def test_main_generates_site(
        self,
        mock_glob,
        mock_read_text,
        mock_write_text,
        mock_mkdir,
        mock_open_file,
        mock_yaml_load,
        mock_format_date,
        mock_copytree,
        mock_copy,
        mock_generate_event_calendars,
        mock_generate_public_calendars,
        mock_generate_webinars_public_calendar,
        mock_generate_rss,
        mock_export_events,
        mock_export_upcoming_events,
        mock_export_webinars,
        mock_export_upcoming_webinars,
        mock_render_event,
        mock_render_webinar,
        mock_render_public_calendars,
        mock_render_webinars_calendar,
    ):
        event_file = Path('events/event1.yml')
        webinar_file = Path('webinars/webinar1.yml')

        mock_glob.side_effect = [
            [event_file],
            [webinar_file],
        ]

        mock_yaml_load.side_effect = [
            {
                'title': 'Конференция',
                'date': '2099-01-01',
                'city': 'Москва',
                'description': 'Описание события',
                'icon': 'event.png',
            },
            {
                'title': 'Вебинар',
                'date': '2099-02-01',
                'description': 'Описание вебинара',
                'pic': 'webinar.png',
                'url': 'https://youtube.com/test',
            },
        ]

        mock_read_text.return_value = (
            '{{ events }}\n'
            '{{ webinars }}\n'
            '{{ public_calendars }}\n'
            '{{ webinars_calendar }}\n'
            '{{ builddate }}'
        )

        mock_render_event.return_value = '<div>EVENT</div>'
        mock_render_webinar.return_value = '<div>WEBINAR</div>'
        mock_render_public_calendars.return_value = '<div>CALENDARS</div>'
        mock_render_webinars_calendar.return_value = '<div>WEBINARS_CALENDAR</div>'
        mock_generate_public_calendars.return_value = ['calendar.ics']
        mock_generate_webinars_public_calendar.return_value = 'webinars.ics'
        mock_generate_rss.return_value = '<rss></rss>'
        mock_format_date.return_value = '11 мая 2026'

        create_web.main()

        mock_read_text.assert_called_once_with(encoding='utf-8')

        assert mock_mkdir.called

        mock_copytree.assert_any_call('img', 'site/img', dirs_exist_ok=True)
        mock_copytree.assert_any_call('icons', 'site/icons', dirs_exist_ok=True)
        mock_copy.assert_called_once_with('web/sw.js', create_web.OUTPUT_DIR / 'sw.js')

        assert mock_generate_event_calendars.call_count == 2

        mock_export_events.assert_called_once()
        mock_export_upcoming_events.assert_called_once()
        mock_export_webinars.assert_called_once()
        mock_export_upcoming_webinars.assert_called_once()

        mock_generate_rss.assert_called_once()

        mock_render_event.assert_called_once()
        mock_render_webinar.assert_called_once()

        assert mock_write_text.called

        final_html = mock_write_text.call_args_list[-1][0][0]

        assert '<div>EVENT</div>' in final_html
        assert '<div>WEBINAR</div>' in final_html
        assert '11 мая 2026' in final_html

    @patch('builtins.print')
    @patch('create_web.yaml.safe_load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.glob')
    def test_main_handles_invalid_yaml(
        self,
        mock_glob,
        mock_read_text,
        mock_open_file,
        mock_yaml_load,
        mock_print,
    ):
        broken_file = Path('events/broken.yml')

        mock_glob.side_effect = [
            [broken_file],
            [],
        ]

        mock_read_text.return_value = '{{ events }}'

        mock_yaml_load.side_effect = Exception('Ошибка YAML')

        with (
            patch('create_web.shutil.copytree'),
            patch('create_web.shutil.copy'),
            patch('create_web.generate_event_calendars'),
            patch('create_web.generate_public_calendars'),
            patch('create_web.generate_webinars_public_calendar'),
            patch('create_web.generate_rss', return_value='rss'),
            patch('create_web.export_events_to_json'),
            patch('create_web.export_upcoming_events_to_json'),
            patch('create_web.export_webinars_to_json'),
            patch('create_web.export_upcoming_webinars_to_json'),
            patch('create_web.render_public_calendars', return_value=''),
            patch('create_web.render_webinars_calendar', return_value=''),
            patch('create_web.format_date', return_value='16 мая 2026'),
            patch('pathlib.Path.mkdir'),
            patch('pathlib.Path.write_text'),
        ):
            create_web.main()

        mock_print.assert_any_call('Ошибка при чтении файла broken.yml: Ошибка YAML')

    @patch('builtins.print')
    @patch('create_web.yaml.safe_load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.glob')
    def test_main_handles_invalid_webinar_yaml(
        self,
        mock_glob,
        mock_read_text,
        mock_open_file,
        mock_yaml_load,
        mock_print,
    ):
        broken_file = Path('webinars/broken.yml')

        mock_glob.side_effect = [
            [],
            [broken_file],
        ]

        mock_read_text.return_value = '{{ webinars }}'

        mock_yaml_load.side_effect = Exception('Ошибка YAML')

        with (
            patch('create_web.shutil.copytree'),
            patch('create_web.shutil.copy'),
            patch('create_web.generate_event_calendars'),
            patch('create_web.generate_public_calendars'),
            patch('create_web.generate_webinars_public_calendar'),
            patch('create_web.generate_rss', return_value='rss'),
            patch('create_web.export_events_to_json'),
            patch('create_web.export_upcoming_events_to_json'),
            patch('create_web.export_webinars_to_json'),
            patch('create_web.export_upcoming_webinars_to_json'),
            patch('create_web.render_public_calendars', return_value=''),
            patch('create_web.render_webinars_calendar', return_value=''),
            patch('create_web.format_date', return_value='16 мая 2026'),
            patch('pathlib.Path.mkdir'),
            patch('pathlib.Path.write_text'),
        ):
            create_web.main()

        mock_print.assert_any_call('Ошибка при чтении файла broken.yml: Ошибка YAML')
