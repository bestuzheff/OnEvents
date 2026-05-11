import pytest
from utils.dates import russian_count_form, format_months_ru, format_time_until_ru
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


def test_russian_count_form():
    """Тестирует склонение русских существительных."""
    # Тест для форм ("день", "дня", "дней")
    assert russian_count_form(1, ("день", "дня", "дней")) == "день"
    assert russian_count_form(2, ("день", "дня", "дней")) == "дня"
    assert russian_count_form(3, ("день", "дня", "дней")) == "дня"
    assert russian_count_form(4, ("день", "дня", "дней")) == "дня"
    assert russian_count_form(5, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(6, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(10, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(11, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(12, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(13, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(14, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(15, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(16, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(17, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(18, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(19, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(20, ("день", "дня", "дней")) == "дней"
    assert russian_count_form(21, ("день", "дня", "дней")) == "день"
    assert russian_count_form(22, ("день", "дня", "дней")) == "дня"
    assert russian_count_form(23, ("день", "дня", "дней")) == "дня"
    assert russian_count_form(24, ("день", "дня", "дней")) == "дня"
    assert russian_count_form(25, ("день", "дня", "дней")) == "дней"
    
    # Тест для других форм
    assert russian_count_form(1, ("год", "года", "лет")) == "год"
    assert russian_count_form(2, ("год", "года", "лет")) == "года"
    assert russian_count_form(5, ("год", "года", "лет")) == "лет"
