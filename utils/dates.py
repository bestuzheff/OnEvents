"""
Утилиты для работы с датами.
Содержит функции для склонения существительных и форматирования временных интервалов.
"""

from dateutil.relativedelta import relativedelta


def russian_count_form(value: int | float, forms: tuple[str, str, str]) -> str:
    """Возвращает правильную форму существительного для русского языка в зависимости от числа.

    Args:
        value: Число, для которого нужно выбрать форму.
        forms: Кортеж из трех форм: (1, 2-4, 5-0).
               Например: ("день", "дня", "дней") или ("месяц", "месяца", "месяцев").

    Returns:
        Правильная форма существительного.

    Примеры:
        1 -> "день"
        2 -> "дня"
        5 -> "дней"
        11 -> "дней"
        21 -> "день"
    """
    n = abs(int(value))
    n_mod100 = n % 100

    # Исключение для чисел 11-14 (向他们 "дней")
    if 11 <= n_mod100 <= 14:
        return forms[2]

    n_mod10 = n % 10

    # 1 - первая форма (день)
    if n_mod10 == 1:
        return forms[0]
    # 2-4 - вторая форма (дня)
    if 2 <= n_mod10 <= 4:
        return forms[1]
    # остальные - третья форма (дней)
    return forms[2]


def format_months_ru(today_date, target_date) -> tuple[str, str]:
    """Вычисляет количество месяцев между датами и возвращает строку с правильным склонением.

    Args:
        today_date: Текущая дата.
        target_date: Целевая дата.

    Returns:
        Кортеж (количество_месяцев, слово_месяцев).
        Например: ("3", "месяца") или ("1", "месяц").

    Особенности:
        - Показывает только целые месяцы
        - Округление: до 0.5 включительно - вниз, больше 0.5 - вверх
    """
    # Вычисляем разницу в годах и месяцах
    rd = relativedelta(target_date, today_date)
    months_int = rd.years * 12 + rd.months

    # Если прошло меньше месяца
    if months_int <= 0:
        return '0', 'месяцев'

    # Вычисляем остаток дней для более точного округления
    anchor = today_date + relativedelta(months=months_int)
    remainder_days = (target_date - anchor).days
    # Длина текущего месяца (дней в месяце)
    month_len = (anchor + relativedelta(months=1) - anchor).days or 30

    # Вычисляем дробную часть месяца
    months_float = months_int + (remainder_days / month_len)

    # Округляем
    m_floor = int(months_float)
    frac = months_float - m_floor
    m_rounded = m_floor if frac <= 0.5 else (m_floor + 1)

    return str(m_rounded), russian_count_form(m_rounded, ('месяц', 'месяца', 'месяцев'))


def format_time_until_ru(today_date, target_date) -> str:
    """Возвращает строку с временем до события на русском языке.

    Args:
        today_date: Текущая дата.
        target_date: Дата события.

    Returns:
        Строка с временем до события.

    Правила форматирования:
        - Если событие сегодня -> "(сегодня)"
        - Если событие завтра -> "(завтра)"
        - Меньше месяца -> "через X дней"
        - Больше месяца -> "через ~X месяцев"
        - Если округление дало 0 месяцев -> "через X дней"
    """
    days_left = (target_date - today_date).days

    # Событие сегодня или завтра
    if days_left == 0:
        return '(сегодня)'
    if days_left == 1:
        return '(завтра)'

    # Вычисляем общее количество месяцев
    rd = relativedelta(target_date, today_date)
    total_months = rd.years * 12 + rd.months

    # Меньше 1 календарного месяца - показываем дни
    if total_months < 1:
        day_word = russian_count_form(days_left, ('день', 'дня', 'дней'))
        return f'(через {days_left} {day_word})'

    # Вычисляем месяцы с округлением
    months_str, month_word = format_months_ru(today_date, target_date)

    # Если получилось 0 месяцев - показываем дни
    if months_str == '0':
        day_word = russian_count_form(days_left, ('день', 'дня', 'дней'))
        return f'(через {days_left} {day_word})'

    return f'(через ~{months_str} {month_word})'
