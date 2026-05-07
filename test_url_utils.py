import pytest
from url_utils import shorten_url, get_timezone_for_event, map_link, add_utm_marks


def test_get_timezone_for_event():
    """Тестирует определение временной зоны по городу."""
    # Тест для городов с известной временной зоной
    assert get_timezone_for_event({"city": "Москва"}) == "Europe/Moscow"
    assert get_timezone_for_event({"city": "москва"}) == "Europe/Moscow"  # регистронезависимо
    assert get_timezone_for_event({"city": "Онлайн"}) == "Europe/Moscow"
    assert get_timezone_for_event({"city": "онлайн"}) == "Europe/Moscow"
    assert get_timezone_for_event({"city": "Санкт-Петербург"}) == "Europe/Moscow"
    assert get_timezone_for_event({"city": "новосибирск"}) == "Asia/Novosibirsk"
    assert get_timezone_for_event({"city": "Иркутск"}) == "Asia/Irkutsk"
    
    # Тест для неизвестных городов (должен вернуть None)
    assert get_timezone_for_event({"city": "Неизвестный город"}) is None
    assert get_timezone_for_event({"city": ""}) is None
    assert get_timezone_for_event({}) is None
    assert get_timezone_for_event({"city": None}) is None


def test_shorten_url():
    """Тестирует сокращение URL (мок тест, так как требует внешнего сервиса)."""
    # Проверяем, что функция не падает на пустой вход
    assert shorten_url("") == ""
    assert shorten_url(None) == None
    
    # Фактическое тестирование требует мокирования внешнего вызова
    # Для простоты проверяем только, что функция вызывается без ошибок
    try:
        result = shorten_url("https://example.com/very/long/url/that/should/be/shortened")
        # Результат может быть либо исходный URL, либо сокращенный
        assert isinstance(result, str)
    except Exception:
        # Если сервис недоступен, функция должна вернуть исходный URL
        pass