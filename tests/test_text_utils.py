import unittest

from utils.text import clean_text, to_hhmmss, make_slug


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

