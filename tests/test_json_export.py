import pytest
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


@pytest.fixture
def event():
    return {
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


@pytest.fixture
def webinar():
    return {
        'id': 'webinar-1',
        'title': 'Python Webinar',
        'date': '2026-05-10',
        'pic': 'webinar.png',
        'description': 'Webinar description',
        'url': 'https://webinar.example.com',
        'sessions': [{'title': 'Intro'}],
    }


@pytest.fixture
def output_dir():
    return Path('/tmp')


def test_serialize_event(event):
    result = serialize_event(event)

    assert result['id'] == 'event-1'
    assert result['title'] == 'Conference'
    assert result['icon'] == 'img/events/event.png'
    assert result['registration_url'] == 'https://register.example.com'
    assert result['url'] == 'https://event.example.com'
    assert result['sessions'] == [{'title': 'Session 1'}]


def test_serialize_event_without_optional_fields():
    event = {
        'id': 'event-2',
        'title': 'Simple Event',
        'date': '2026-05-01',
        'description': 'Description',
    }

    result = serialize_event(event)

    assert 'registration_url' not in result
    assert 'url' not in result
    assert 'sessions' not in result
    assert result['icon'] == ''


def test_serialize_webinar(webinar):
    result = serialize_webinar(webinar)

    assert result['id'] == 'webinar-1'
    assert result['title'] == 'Python Webinar'
    assert result['pic'] == 'img/webinars/webinar.png'
    assert result['url'] == 'https://webinar.example.com'
    assert result['sessions'] == [{'title': 'Intro'}]


def test_serialize_webinar_without_optional_fields():
    webinar = {
        'id': 'webinar-2',
        'title': 'Simple Webinar',
        'date': '2026-05-11',
        'description': 'Description',
    }

    result = serialize_webinar(webinar)

    assert 'url' not in result
    assert 'sessions' not in result
    assert result['pic'] == ''


@patch('json_export.json.json.dump')
@patch('builtins.open', new_callable=mock_open)
def test_export_to_json(
    mock_file,
    mock_json_dump,
    event,
    output_dir,
):
    result = export_to_json(
        items=[event],
        output_dir=output_dir,
        filename='events.json',
        serializer=serialize_event,
    )

    expected_path = output_dir / 'events.json'

    assert result == expected_path

    mock_file.assert_called_once_with(expected_path, 'w', encoding='utf-8')

    mock_json_dump.assert_called_once()

    dumped_data = mock_json_dump.call_args[0][0]

    assert dumped_data[0]['id'] == 'event-1'
    assert dumped_data[0]['icon'] == 'img/events/event.png'


@patch('json_export.json.export_to_json')
def test_export_events_to_json(mock_export, event, output_dir):
    mock_export.return_value = output_dir / 'events.json'

    result = export_events_to_json([event], output_dir)

    assert result == output_dir / 'events.json'

    mock_export.assert_called_once_with(
        items=[event],
        output_dir=output_dir,
        filename='events.json',
        serializer=serialize_event,
    )


@patch('json_export.json.export_to_json')
def test_export_upcoming_events_to_json(mock_export, event, output_dir):
    mock_export.return_value = output_dir / 'events_upcoming.json'

    result = export_upcoming_events_to_json([event], output_dir)

    assert result == output_dir / 'events_upcoming.json'

    mock_export.assert_called_once_with(
        items=[event],
        output_dir=output_dir,
        filename='events_upcoming.json',
        serializer=serialize_event,
    )


@patch('json_export.json.export_to_json')
def test_export_webinars_to_json(mock_export, webinar, output_dir):
    mock_export.return_value = output_dir / 'webinars.json'

    result = export_webinars_to_json([webinar], output_dir)

    assert result == output_dir / 'webinars.json'

    mock_export.assert_called_once_with(
        items=[webinar],
        output_dir=output_dir,
        filename='webinars.json',
        serializer=serialize_webinar,
    )


@patch('json_export.json.export_to_json')
def test_export_upcoming_webinars_to_json(mock_export, webinar, output_dir):
    mock_export.return_value = output_dir / 'webinars_upcoming.json'

    result = export_upcoming_webinars_to_json([webinar], output_dir)

    assert result == output_dir / 'webinars_upcoming.json'

    mock_export.assert_called_once_with(
        items=[webinar],
        output_dir=output_dir,
        filename='webinars_upcoming.json',
        serializer=serialize_webinar,
    )
