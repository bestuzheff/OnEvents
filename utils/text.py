"""
Утилиты для работы с текстом.
Содержит функции для очистки текста, формирования URL-слагов и преобразования времени.
"""

import re

# Регулярные выражения для обработки текста
# Удаляет все символы, кроме букв, цифр, пробелов и дефисов
SAFE_CHARS_PATTERN = re.compile(r'[^\w\s-]')
# Заменяет множественные пробелы и дефисы на один дефис
DASHES_SPACES_PATTERN = re.compile(r'[-\s]+')


def clean_text(text: str) -> str:
    """Очищает текст от HTML тегов и экранирует специальные символы для ICS формата.

    Args:
        text: Исходный текст с возможными HTML тегами.

    Returns:
        Очищенный текст без HTML тегов и с экранированными спецсимволами.
    """
    # Убираем все HTML теги (например <br>, <a>, <p>)
    text = re.sub(r'<[^>]+>', '', text)
    # Экранируем специальные символы для ICS файлов
    text = text.replace('\\', '\\\\')  # Обратный слеш
    text = text.replace(',', '\\,')  # Запятая
    text = text.replace(';', '\\;')  # Точка с запятой
    text = text.replace('\n', '\\n')  # Перенос строки
    return text


def make_slug(text: str) -> str:
    """Создает безопасный URL-слаг из названия (например для имени файла).

    Args:
        text: Название, которое нужно преобразовать в слаг.

    Returns:
        Слаг - строка в нижнем регистре с дефисами вместо пробелов.
    """
    # Удаляем небезопасные символы
    safe = SAFE_CHARS_PATTERN.sub('', str(text)).strip()
    # Заменяем пробелы и множественные дефисы на один дефис
    safe = DASHES_SPACES_PATTERN.sub('-', safe)
    return safe.lower()


def to_hhmmss(time_str: str) -> str:
    """Преобразует время в формат HHMMSS для ICS файлов.

    Args:
        time_str: Время в формате HH:MM или HH:MM:SS.

    Returns:
        Время в формате HHMMSS (например "14:30" -> "143000").
    """
    time_str = str(time_str).strip()
    # Заменяем точки на двоеточия (в некоторых YAML могут быть "14.30")
    time_str = time_str.replace('.', ':')
    parts = time_str.split(':')

    # Если указан только час
    if len(parts) == 1:
        hour = parts[0]
        minute = '00'
    else:
        hour = parts[0]
        minute = parts[1]

    # Дополняем до двух цифр
    hour = hour.zfill(2)
    minute = minute.zfill(2)
    return f'{hour}{minute}00'
