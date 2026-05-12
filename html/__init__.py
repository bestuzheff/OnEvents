"""
Публичный API пакета генерации HTML карточек.
"""

from .cards import (
    generate_event_id,
    render_event,
    render_webinar,
)

__all__ = [
    'generate_event_id',
    'render_event',
    'render_webinar',
]
