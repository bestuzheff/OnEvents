import unittest
from datetime import date

from utils.dates import (
    format_months_ru,
    format_time_until_ru,
    russian_count_form,
)


class TestDateUtils(unittest.TestCase):
    def test_russian_count_form_days(self):
        """Тестирует склонение для слова 'день'."""
        test_cases = [
            (1, 'день'),
            (2, 'дня'),
            (3, 'дня'),
            (4, 'дня'),
            (5, 'дней'),
            (6, 'дней'),
            (10, 'дней'),
            (11, 'дней'),
            (12, 'дней'),
            (13, 'дней'),
            (14, 'дней'),
            (15, 'дней'),
            (16, 'дней'),
            (17, 'дней'),
            (18, 'дней'),
            (19, 'дней'),
            (20, 'дней'),
            (21, 'день'),
            (22, 'дня'),
            (23, 'дня'),
            (24, 'дня'),
            (25, 'дней'),
        ]

        for number, expected in test_cases:
            with self.subTest(number=number):
                self.assertEqual(
                    russian_count_form(number, ('день', 'дня', 'дней')), expected
                )

    def test_russian_count_form_years(self):
        """Тестирует склонение для слова 'год'."""
        self.assertEqual(russian_count_form(1, ('год', 'года', 'лет')), 'год')
        self.assertEqual(russian_count_form(2, ('год', 'года', 'лет')), 'года')
        self.assertEqual(russian_count_form(5, ('год', 'года', 'лет')), 'лет')

    def test_format_months_ru(self):
        self.assertEqual(
            format_months_ru(date(2026, 5, 1), date(2026, 5, 20)), ('0', 'месяцев')
        )
        self.assertEqual(
            format_months_ru(date(2026, 5, 1), date(2026, 6, 25)), ('2', 'месяца')
        )
        self.assertEqual(
            format_months_ru(date(2026, 5, 1), date(2026, 6, 10)), ('1', 'месяц')
        )

    def test_format_time_until_ru(self):
        self.assertIn(
            'через', format_time_until_ru(date(2026, 5, 11), date(2026, 5, 21))
        )
