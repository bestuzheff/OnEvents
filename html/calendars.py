"""
Генерация HTML блоков для публичных календарей.
Содержит функции для рендеринга секций с ссылками на подписку календарей.
"""


def render_public_calendars(public_calendars: list[tuple[str, str, str]]) -> str:
    """Генерирует HTML блок с публичными календарями для подписки.

    Args:
        public_calendars: Список кортежей (название, URL, город).

    Returns:
        HTML код блока с инструкцией и ссылками на календари.

    Структура:
        - Заголовок "Подписка на календарь"
        - Инструкция по подписке (2 шага)
        - Список календарей с полем ввода URL и кнопкой копирования

    Note:
        Используется для отображения на странице сайта в секции "Календари".
    """
    calendars_html = []
    for name, url, city in public_calendars:
        calendars_html.append(f"""
    <div class="calendar-item" data-city="{city}">
        <div class="calendar-city-name">{name}</div>
        <div class="calendar-input-group">
            <input type="text" class="calendar-input" value="{url}" readonly>
            <button class="calendar-copy-btn" title="Копировать ссылку">🔗</button>
        </div>
    </div>""")

    return f"""
    <h2>🔗 Подписка на календарь</h2>

    <article class="card">
        <p>Чтобы всегда быть в курсе событий подпишитесь на календарь в вашем приложении-календаре. События будут автоматически обновляться при добавлении на сайт.</p>
        <ol>
            <li>Скопируйте ссылку календаря</li>
            <li>В приложении календаря выберите "Добавить календарь подписки" (для Apple) или "Добавить календарь по URL" (для Google)</li>
        </ol>
        {''.join(calendars_html)}
    </article>
    """


def render_webinars_calendar(webinars_calendar_url: str) -> str:
    """Генерирует HTML блок подписки на календарь вебинаров.

    Args:
        webinars_calendar_url: URL календаря вебинаров.

    Returns:
        HTML код блока с ссылкой на календарь вебинаров.

    Note:
        Вебинары хранятся в отдельном календаре, так как они не привязаны к городам
        и имеют другой формат (трансляции, а не офлайн мероприятия).
    """
    return f"""
    <article class="card">
        <p>Подпишитесь на отдельный календарь с вебинарами из раздела «Прямой эфир».</p>
        <div class="calendar-item" data-city="">
            <div class="calendar-city-name">Прямой эфир</div>
            <div class="calendar-input-group">
                <input type="text" class="calendar-input" value="{webinars_calendar_url}" readonly>
                <button class="calendar-copy-btn" title="Копировать ссылку">🔗</button>
            </div>
        </div>
    </article>
    """