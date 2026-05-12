"""
Публичный API пакета ICS календарей.
"""

from .vevents import (
    generate_event_vevent,
    generate_public_calendar,
    generate_ics_content,
)

__all__ = [
    'generate_event_vevent',
    'generate_public_calendar',
    'generate_ics_content',
]
