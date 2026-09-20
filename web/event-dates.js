(function (root, factory) {
  var api = factory();

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }

  if (root && root.document) {
    api.updateEventDates(root.document, new Date());
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  var DAY_MS = 24 * 60 * 60 * 1000;

  function dayNumber(date) {
    return Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / DAY_MS;
  }

  function parseLocalDate(value) {
    var parts = value.split('-').map(Number);
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }

  function countForm(value, forms) {
    var number = Math.abs(value);
    var lastTwo = number % 100;
    if (lastTwo >= 11 && lastTwo <= 14) {
      return forms[2];
    }
    var last = number % 10;
    if (last === 1) {
      return forms[0];
    }
    if (last >= 2 && last <= 4) {
      return forms[1];
    }
    return forms[2];
  }

  function addMonths(date, months) {
    var year = date.getFullYear();
    var month = date.getMonth() + months;
    var day = date.getDate();
    var lastDay = new Date(year, month + 1, 0).getDate();
    return new Date(year, month, Math.min(day, lastDay));
  }

  function fullMonthsBetween(today, target) {
    var months = (target.getFullYear() - today.getFullYear()) * 12 + target.getMonth() - today.getMonth();
    if (addMonths(today, months) > target) {
      months -= 1;
    }
    return months;
  }

  function formatTimeUntil(today, target) {
    var daysLeft = dayNumber(target) - dayNumber(today);
    if (daysLeft === 0) {
      return '(сегодня)';
    }
    if (daysLeft === 1) {
      return '(завтра)';
    }

    var months = fullMonthsBetween(today, target);
    if (months < 1) {
      return '(через ' + daysLeft + ' ' + countForm(daysLeft, ['день', 'дня', 'дней']) + ')';
    }

    var anchor = addMonths(today, months);
    var nextAnchor = addMonths(anchor, 1);
    var remainder = dayNumber(target) - dayNumber(anchor);
    var monthLength = dayNumber(nextAnchor) - dayNumber(anchor);
    var roundedMonths = remainder / monthLength > 0.5 ? months + 1 : months;
    return '(через ~' + roundedMonths + ' ' + countForm(roundedMonths, ['месяц', 'месяца', 'месяцев']) + ')';
  }

  function updateEventDates(documentRoot, now) {
    var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    documentRoot.querySelectorAll('#events article.card time[datetime]').forEach(function (time) {
      var target = parseLocalDate(time.dateTime);
      var card = time.closest('article.card');
      if (dayNumber(target) < dayNumber(today)) {
        card.remove();
        return;
      }
      var label = time.querySelector('.days-left');
      if (label) {
        label.textContent = formatTimeUntil(today, target);
      }
    });
  }

  return {
    formatTimeUntil: formatTimeUntil,
    updateEventDates: updateEventDates
  };
});
