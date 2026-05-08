from __future__ import annotations

from collections.abc import Callable
from collections import Counter
from datetime import date, datetime
import xml.sax.saxutils as saxutils

from babel.dates import format_date


def is_online_event(event: dict) -> bool:
    return str(event.get('city', '')).strip().lower() in ('online', 'онлайн')


def unique_offline_cities(items: list[dict]) -> list[str]:
    return sorted(
        {
            str(event.get('city', '')).strip()
            for event in items
            if event.get('city') and not is_online_event(event)
        },
        key=lambda city: city.lower(),
    )


def event_date_value(event: dict) -> date:
    return datetime.strptime(event['date'], '%Y-%m-%d').date()


def safe_subtract_year(d: date, years: int = 1) -> date:
    """Вычитает годы, аккуратно обрабатывая 29 февраля."""
    try:
        return d.replace(year=d.year - years)
    except ValueError:
        # 29 февраля -> 28 февраля
        return d.replace(year=d.year - years, day=28)


def month_start(d: date) -> date:
    return d.replace(day=1)


def add_months(d: date, months: int) -> date:
    """Возвращает дату с сдвигом на N месяцев (день всегда 1)."""
    base = month_start(d)
    month_index = (base.year * 12) + (base.month - 1) + months
    year = month_index // 12
    month = (month_index % 12) + 1
    return date(year, month, 1)


def render_metric_card(value, label: str, note: str = '') -> str:
    note_html = f'<small>{saxutils.escape(note)}</small>' if note else ''
    return f"""
      <article class="metric-card">
        <strong>{value}</strong>
        <span>{saxutils.escape(label)}</span>
        {note_html}
      </article>"""


def render_bar_rows(rows: list[tuple[str, int]], max_value: int | None = None) -> str:
    max_count = max_value or max((value for _, value in rows), default=1)
    html = []
    for name, value in rows:
        width = max(4, round((value / max_count) * 100)) if max_count else 0
        html.append(
            f"""
          <div class="bar-row">
            <span>{saxutils.escape(str(name))}</span>
            <i aria-hidden="true"><b style="width:{width}%"></b></i>
            <strong>{value}</strong>
          </div>"""
        )
    return ''.join(html)


def render_month_heatmap(all_items: list[dict], base_year: int) -> str:
    month_counter = Counter(event_date_value(event).month for event in all_items)
    max_count = max(month_counter.values(), default=1)
    cells = []
    for month in range(1, 13):
        value = month_counter.get(month, 0)
        intensity = 0.14 + (value / max_count) * 0.86 if value else 0.08
        month_name = format_date(date(base_year, month, 1), format='LLL', locale='ru')
        cells.append(
            f"""
          <div class="month-cell" style="--heat:{intensity:.2f}">
            <span>{month_name}</span>
            <strong>{value}</strong>
          </div>"""
        )
    return ''.join(cells)


def render_recent_months(all_items: list[dict], today_date: date) -> str:
    month_counter = Counter(event_date_value(event).strftime('%Y-%m') for event in all_items)
    months = []
    first_month = add_months(today_date, -11)
    for offset in range(12):
        month_date = add_months(first_month, offset)
        key = month_date.strftime('%Y-%m')
        label = format_date(month_date, format='LLL y', locale='ru')
        months.append((label, month_counter.get(key, 0)))
    return render_bar_rows(months)


def render_statistics_section(
    all_events: list[dict],
    future_events: list[dict],
    all_webinars: list[dict],
    today_date: date,
    russian_count_form: Callable[[int | float, tuple[str, str, str]], str],
) -> str:
    last_year_start = safe_subtract_year(today_date, 1)
    past_events = [event for event in all_events if event_date_value(event) < today_date]
    last_year_events = [event for event in past_events if event_date_value(event) >= last_year_start]
    past_offline_events = [event for event in past_events if not is_online_event(event)]
    past_online_events = [event for event in past_events if is_online_event(event)]

    last_year_cities = unique_offline_cities(last_year_events)
    future_cities = unique_offline_cities(future_events)
    past_cities = unique_offline_cities(past_events)

    city_counter = Counter(str(event.get('city', '')).strip() for event in past_offline_events)
    city_rows = render_bar_rows(city_counter.most_common(10))

    year_counter = Counter(event_date_value(event).year for event in past_events)
    year_rows = render_bar_rows([(str(year), count) for year, count in sorted(year_counter.items())])

    format_rows = render_bar_rows(
        [
            ('Офлайн', len(past_offline_events)),
            ('Онлайн', len(past_online_events)),
            ('Прямой эфир', len(all_webinars)),
        ],
        max_value=max(len(past_offline_events), len(past_online_events), len(all_webinars), 1),
    )

    recent_events = sorted(past_events, key=lambda event: event['date'], reverse=True)[:10]
    recent_html = []
    for event in recent_events:
        event_date = event_date_value(event)
        recent_html.append(
            f"""
          <li>
            <time datetime="{event['date']}">{format_date(event_date, format='d MMM', locale='ru')}</time>
            <div>
              <span>{saxutils.escape(event['title'])}</span>
              <small>{saxutils.escape(str(event.get('city', '')).strip())}</small>
            </div>
          </li>"""
        )

    return f"""
  <section id="statistics" class="statistics-section">
    <h2>Статистика</h2>
    <div class="statistics-metrics">
    {render_metric_card(len(past_events), 'уже проведено', f"{len(past_cities)} {russian_count_form(len(past_cities), ('город', 'города', 'городов'))}")}
    {render_metric_card(len(all_events), 'всего событий', 'прошедшие и будущие')}
    {render_metric_card(len(past_online_events), 'онлайн-события', 'без учета вебинаров')}
    {render_metric_card(len(future_events), 'в будущей афише', f"{len(future_cities)} {russian_count_form(len(future_cities), ('город', 'города', 'городов'))}")}
    {render_metric_card(len(last_year_events), 'за последний год', f"{len(last_year_cities)} {russian_count_form(len(last_year_cities), ('город', 'города', 'городов'))}")}
    {render_metric_card(len(all_webinars), 'вебинаров', 'раздел Прямой эфир')}
    </div>

    <div class="statistics-layout">
    <div>
      <article class="statistics-panel">
        <h2>Самые активные города</h2>
        {city_rows}
      </article>
      <article class="statistics-panel">
        <h2>Сезонность по месяцам</h2>
        <div class="month-grid">{render_month_heatmap(all_events, today_date.year)}</div>
      </article>
      <article class="statistics-panel">
        <h2>Последние 12 месяцев</h2>
        {render_recent_months(all_events, today_date)}
      </article>
    </div>
    <aside>
      <article class="statistics-panel">
        <h2>Форматы</h2>
        {format_rows}
      </article>
      <article class="statistics-panel">
        <h2>По годам</h2>
        {year_rows}
      </article>
      <article class="statistics-panel">
        <h2>Последние прошедшие</h2>
        <ul class="recent-list">{''.join(recent_html)}</ul>
      </article>
    </aside>
    </div>
  </section>"""

