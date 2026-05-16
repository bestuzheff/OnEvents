from utils.text import clean_text, make_slug, to_hhmmss


class TestTextUtils:
    def test_clean_text_strips_html(self):
        assert clean_text('<br>') == ''
        assert clean_text('<a>hello</a>') == 'hello'

    def test_to_hhmmss(self):
        assert to_hhmmss('22:00') == '220000'
        assert to_hhmmss('9') == '090000'
        assert to_hhmmss('9.05') == '090500'

    def test_make_slug(self):
        assert make_slug(' Санкт-Петербург ') == 'санкт-петербург'
