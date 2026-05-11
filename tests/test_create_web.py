import unittest

from utils.text import clean_text, to_hhmmss, make_slug
from utils.dates import russian_count_form, format_time_until_ru, format_months_ru
from datetime import date


class TestTextUtils(unittest.TestCase):
    def test_clean_text_strips_html(self):
        self.assertEqual(clean_text("<br>"), "")
        self.assertEqual(clean_text("<a>hello</a>"), "hello")

    def test_to_hhmmss(self):
        self.assertEqual(to_hhmmss("22:00"), "220000")
        self.assertEqual(to_hhmmss("9"), "090000")
        self.assertEqual(to_hhmmss("9.05"), "090500")

    def test_make_slug(self):
        self.assertEqual(make_slug(" Санкт-Петербург "), "санкт-петербург")


class TestDateUtils(unittest.TestCase):
    def test_russian_count_form(self):
        self.assertEqual(russian_count_form(1, ("день", "дня", "дней")), "день")
        self.assertEqual(russian_count_form(2, ("день", "дня", "дней")), "дня")
        self.assertEqual(russian_count_form(5, ("день", "дня", "дней")), "дней")
        self.assertEqual(russian_count_form(11, ("день", "дня", "дней")), "дней")
        self.assertEqual(russian_count_form(21, ("день", "дня", "дней")), "день")
    
    def test_format_months_less_than_month(self):
        self.assertEqual(format_months_ru(date(2026, 5, 1), date(2026, 5, 20)), ("0", "месяцев"))
        self.assertEqual(format_months_ru(date(2026, 5, 1), date(2026, 6, 25)), ("2", "месяца"))
        self.assertEqual(format_months_ru(date(2026, 5, 1), date(2026, 6, 10)), ("1", "месяц"))


class TestCreateWebCalendarAndRender(unittest.TestCase):
     def test_format_time_until_ru(self):
        self.assertIn(
            "через",
            format_time_until_ru(date(2026, 5, 11), date(2026, 5, 21))
        )