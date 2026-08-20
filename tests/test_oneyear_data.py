from datetime import date
from unittest.mock import patch

import create_web


def make_event(**overrides):
    event = {
        'title': 'Тестовая встреча',
        'date': '2025-09-15',
        'city': 'Москва',
        'description': 'Практическая встреча для разработчиков 1С',
        'icon': 'test.jpg',
    }
    event.update(overrides)
    return event


def make_webinar(**overrides):
    webinar = {
        'title': 'Тестовый вебинар',
        'date': '2025-09-20',
        'description': 'Обсудим вопросы разработки',
        'pic': 'webinar.jpg',
    }
    webinar.update(overrides)
    return webinar


class TestParseItemDate:
    def test_parses_valid_date(self):
        assert create_web._parse_item_date({'date': '2025-09-15'}) == date(2025, 9, 15)

    def test_returns_none_for_missing_date(self):
        assert create_web._parse_item_date({}) is None

    def test_returns_none_for_invalid_date(self):
        assert create_web._parse_item_date({'date': 'not-a-date'}) is None


class TestIsOnlineCity:
    def test_empty_city_is_online(self):
        assert create_web._is_online_city('') is True

    def test_online_variants(self):
        assert create_web._is_online_city('Online') is True
        assert create_web._is_online_city('Онлайн') is True
        assert create_web._is_online_city('  онлайн  ') is True

    def test_real_city_is_not_online(self):
        assert create_web._is_online_city('Москва') is False


class TestRuPlural:
    def test_one(self):
        assert create_web.ru_plural(1, 'город', 'города', 'городов') == 'город'

    def test_few(self):
        assert create_web.ru_plural(3, 'город', 'города', 'городов') == 'города'

    def test_many(self):
        assert create_web.ru_plural(5, 'город', 'города', 'городов') == 'городов'

    def test_eleven_is_many(self):
        assert create_web.ru_plural(11, 'город', 'города', 'городов') == 'городов'


class TestMonthRange:
    def test_single_month(self):
        assert create_web.month_range(date(2025, 8, 21), date(2025, 8, 31)) == [(2025, 8)]

    def test_spans_year_boundary(self):
        result = create_web.month_range(date(2025, 12, 1), date(2026, 2, 1))
        assert result == [(2025, 12), (2026, 1), (2026, 2)]


class TestBuildHeatmapData:
    def test_counts_events_within_range(self):
        events = [make_event(date='2025-09-15'), make_event(date='2025-09-15')]
        data = create_web.build_heatmap_data(events, [])

        total = sum(c['count'] for c in data['cells'] if c['count'] is not None)
        assert total == 2
        assert data['weeks'] > 0
        assert data['months'][0]['label'] == 'авг'

    def test_ignores_events_outside_range(self):
        events = [make_event(date='2020-01-01')]
        data = create_web.build_heatmap_data(events, [])
        total = sum(c['count'] for c in data['cells'] if c['count'] is not None)
        assert total == 0

    def test_ignores_events_without_date(self):
        events = [make_event(date='not-a-date')]
        data = create_web.build_heatmap_data(events, [])
        total = sum(c['count'] for c in data['cells'] if c['count'] is not None)
        assert total == 0

    def test_month_spans_sum_to_weeks(self):
        data = create_web.build_heatmap_data([], [])
        assert sum(m['span'] for m in data['months']) == data['weeks']


class TestBuildMonthlyData:
    def test_splits_offline_online_webinars(self):
        events = [
            make_event(date='2025-09-15', city='Москва'),
            make_event(date='2025-09-16', city='Online'),
        ]
        webinars = [make_webinar(date='2025-09-17')]

        data = create_web.build_monthly_data(events, webinars)
        sept = next(m for m in data if m['label'] == 'сен')

        assert sept['total'] == 3
        assert sept['offline'] == 1
        assert sept['online'] == 1
        assert sept['webinars'] == 1

    def test_covers_start_to_end_chronologically(self):
        data = create_web.build_monthly_data([], [])
        expected = create_web.month_range(create_web.ONEYEAR_START, create_web.ONEYEAR_END)
        assert [(m['year'], create_web.MONTH_SHORT_RU.index(m['label']) + 1) for m in data] == expected

    def test_keeps_same_month_in_different_years_separate(self):
        events = [make_event(date='2025-08-25', city='Москва'), make_event(date='2026-08-05', city='Москва')]
        data = create_web.build_monthly_data(events, [])
        august_buckets = [m for m in data if m['label'] == 'авг']
        assert sum(m['total'] for m in august_buckets) == 2
        assert all(m['total'] <= 1 for m in august_buckets)


class TestBuildGeoData:
    def test_counts_and_ranks_cities(self):
        events = [make_event(city='Москва'), make_event(city='Москва'), make_event(city='Казань')]
        data = create_web.build_geo_data(events, top_n=8)

        assert data[0]['city'] == 'Москва'
        assert data[0]['count'] == 2

    def test_excludes_online_events(self):
        events = [make_event(city='Онлайн')]
        data = create_web.build_geo_data(events)
        assert data == []

    def test_groups_rest_beyond_top_n(self):
        events = [make_event(city=f'Город{i}') for i in range(10)]
        data = create_web.build_geo_data(events, top_n=8)

        assert len(data) == 9
        assert data[-1]['city'].startswith('Ещё 2 город')
        assert data[-1]['count'] == 2
        assert len(data[-1]['cities']) == 2


class TestBuildCityArms:
    def test_returns_full_paths(self):
        arms = create_web.build_city_arms()
        assert arms['Москва'] == '/img/cities/moskva.png'
        assert all(path.startswith('/img/cities/') for path in arms.values())


class TestBuildGraphData:
    def test_includes_only_offline_events_in_range(self):
        events = [
            make_event(city='Москва', date='2025-09-15'),
            make_event(city='Онлайн', date='2025-09-15'),
            make_event(city='Москва', date='2020-01-01'),
        ]
        data = create_web.build_graph_data(events)

        assert len(data) == 1
        assert data[0]['city'] == 'Москва'
        assert data[0]['icon'] == '/img/events/test.jpg'

    def test_uses_default_icon(self):
        event = make_event(city='Москва')
        del event['icon']
        data = create_web.build_graph_data([event])
        assert data[0]['icon'] == '/img/events/default.jpg'


class TestBuildRecentEvents:
    def test_returns_past_events_sorted_desc(self):
        events = [make_event(date='2020-01-01'), make_event(date='2020-06-01')]
        data = create_web.build_recent_events(events, [], limit=10)

        assert [item['date'] for item in data] == ['2020-06-01', '2020-01-01']

    def test_excludes_future_events(self):
        events = [make_event(date='2099-01-01')]
        data = create_web.build_recent_events(events, [], limit=10)
        assert data == []

    def test_webinars_are_always_online(self):
        webinars = [make_webinar(date='2020-01-01')]
        data = create_web.build_recent_events([], webinars, limit=10)
        assert data[0]['city'] == 'Онлайн'
        assert data[0]['icon'] == '/img/webinars/webinar.jpg'

    def test_respects_limit(self):
        events = [make_event(date=f'2020-01-{day:02d}') for day in range(1, 15)]
        data = create_web.build_recent_events(events, [], limit=5)
        assert len(data) == 5


class TestWordCloudLemma:
    def test_merges_word_forms(self):
        assert create_web._word_cloud_lemma('клуба') == 'клуб'
        assert create_web._word_cloud_lemma('встречу') == 'встреча'

    def test_verbs_go_to_infinitive(self):
        assert create_web._word_cloud_lemma('обсудим') == 'обсудить'

    def test_filters_stopwords(self):
        assert create_web._word_cloud_lemma('для') is None

    def test_filters_short_words(self):
        assert create_web._word_cloud_lemma('вк') is None

    def test_keeps_1c_literal(self):
        assert create_web._word_cloud_lemma('1с') == '1с'

    def test_applies_manual_override(self):
        assert create_web._word_cloud_lemma('митапа') == 'митап'


class TestBuildWordCloud:
    def test_counts_and_merges_forms(self):
        events = [
            make_event(date='2025-09-15', title='Встреча клуба', description='Обсудим вопросы разработки'),
            make_event(date='2025-09-16', title='Встреча', description='Поговорим про клуб разработчиков'),
        ]
        data = create_web.build_word_cloud(events, [], limit=50)
        words = {w['text']: w['count'] for w in data}

        assert words['встреча'] == 2
        assert words['клуб'] == 2

    def test_ignores_items_outside_range(self):
        events = [make_event(date='2020-01-01', title='Слово', description='')]
        data = create_web.build_word_cloud(events, [], limit=50)
        assert data == []

    def test_respects_limit(self):
        # WORD_RE не захватывает цифры, поэтому берём разные словарные слова,
        # а не "слово0".."словоN" — иначе все схлопнутся в один токен.
        words = ['банк', 'парк', 'дом', 'лес', 'сад', 'мир', 'сон', 'путь', 'день', 'ночь', 'утро', 'век']
        description = ' '.join(words)
        events = [make_event(date='2025-09-15', title='', description=description)]
        data = create_web.build_word_cloud(events, [], limit=10)
        assert len(data) == 10


class TestBuildYearStats:
    def test_counts_offline_online_and_cities(self):
        events = [
            make_event(date='2025-09-15', city='Москва'),
            make_event(date='2025-09-16', city='Москва'),
            make_event(date='2025-09-17', city='Онлайн'),
        ]
        webinars = [make_webinar(date='2025-09-18')]

        stats = create_web.build_year_stats(events, webinars)

        assert stats['total'] == 4
        assert stats['events'] == 3
        assert stats['webinars'] == 1
        assert stats['offline'] == 2
        assert stats['cities'] == 1

    def test_ignores_items_outside_range(self):
        events = [make_event(date='2020-01-01')]
        stats = create_web.build_year_stats(events, [])
        assert stats == {'total': 0, 'events': 0, 'webinars': 0, 'offline': 0, 'cities': 0, 'videos': 0}

    def test_counts_videos_only_for_past_events(self):
        past = make_event(date='2025-09-01', city='Москва')
        past['videos'] = [{'description': 'запись'}]
        future = make_event(date='2026-06-01', city='Москва')
        future['videos'] = [{'description': 'запись'}]

        # "Сегодня" фиксируем, чтобы тест не зависел от реальной даты запуска.
        with patch('create_web.date') as mock_date:
            mock_date.today.return_value = date(2026, 1, 1)
            stats_future = create_web.build_year_stats([future], [])
            stats_past = create_web.build_year_stats([past], [])

        assert stats_future['videos'] == 0
        assert stats_past['videos'] == 1
