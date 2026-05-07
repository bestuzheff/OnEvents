from utils.text import clean_text, to_hhmmss
from utils.dates import russian_count_form, format_time_until_ru
from datetime import date


def test_clean_text():
    assert clean_text("<br>") == ""
    assert clean_text("<a>hello</a>") == "hello"


def test_to_hhmmss():
    assert to_hhmmss("22:00") == "220000"


def test_russian_count_form():
    assert russian_count_form(1, ("день", "дня", "дней")) == "день"
    assert russian_count_form(2, ("день", "дня", "дней")) == "дня"
    assert russian_count_form(5, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(11, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(21, ("день", "дня", "дней")) == "день"
