"""
Публичный API пакета генерации HTML карточек.
"""

from .cards import (
    generate_event_id,
    render_event,
    render_video_card,
    render_webinar,
)

__all__ = [
    'generate_event_id',
    'render_event',
    'render_video_card',
    'render_webinar',
]
