const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

assert.equal(fs.existsSync('web/event-dates.js'), true, 'web/event-dates.js must exist');

const {formatTimeUntil, startEventDates, updateEventDates} = require('../web/event-dates.js');

function localDate(year, month, day) {
  return new Date(year, month - 1, day);
}

assert.equal(formatTimeUntil(localDate(2026, 9, 20), localDate(2026, 9, 20)), '(сегодня)');
assert.equal(formatTimeUntil(localDate(2026, 9, 20), localDate(2026, 9, 21)), '(завтра)');
assert.equal(formatTimeUntil(localDate(2026, 9, 20), localDate(2026, 9, 23)), '(через 3 дня)');
assert.equal(formatTimeUntil(localDate(2026, 9, 20), localDate(2026, 10, 20)), '(через ~1 месяц)');

function eventCard(date) {
  const label = {textContent: ''};
  const card = {removed: false, remove: function () { this.removed = true; }};
  const time = {
    dateTime: date,
    closest: function () { return card; },
    querySelector: function (selector) { return selector === '.days-left' ? label : null; }
  };
  return {card, label, time};
}

const past = eventCard('2026-09-19');
const today = eventCard('2026-09-20');
const future = eventCard('2026-09-23');
const root = {
  querySelectorAll: function () { return [past.time, today.time, future.time]; }
};

updateEventDates(root, localDate(2026, 9, 20));

assert.equal(past.card.removed, true);
assert.equal(today.card.removed, false);
assert.equal(today.label.textContent, '(сегодня)');
assert.equal(future.label.textContent, '(через 3 дня)');

const midnightEvent = eventCard('2026-09-21');
const midnightRoot = {
  querySelectorAll: function () { return [midnightEvent.time]; }
};
const dates = [
  new Date(2026, 8, 20, 23, 59, 59),
  new Date(2026, 8, 21, 0, 0, 1)
];
let scheduledCallback;
let scheduledDelay;

startEventDates(
  midnightRoot,
  function () { return dates.shift(); },
  function (callback, delay) {
    scheduledCallback = callback;
    scheduledDelay = delay;
  }
);

assert.equal(midnightEvent.label.textContent, '(завтра)');
assert.equal(scheduledDelay, 2000);
scheduledCallback();
assert.equal(midnightEvent.label.textContent, '(сегодня)');

const template = fs.readFileSync('web/index.html', 'utf8');
const cityFilterBody = template
  .split('(function cityFilterInit(){')[1]
  .split('})();')[0];
const documentListeners = {};
let cityCards = [
  {city: 'Москва', style: {}, getAttribute: function () { return this.city; }},
  {city: 'Казань', style: {}, getAttribute: function () { return this.city; }}
];
const citySelect = {
  value: 'Москва',
  options: [{value: ''}],
  appendChild: function (option) { this.options.push(option); },
  remove: function (index) { this.options.splice(index, 1); },
  addEventListener: function () {}
};
const cityDocument = {
  readyState: 'complete',
  addEventListener: function (name, callback) { documentListeners[name] = callback; },
  createElement: function () { return {}; },
  getElementById: function (id) { return id === 'cityFilter' ? citySelect : null; },
  querySelectorAll: function (selector) {
    return selector === 'article.card[data-city]' ? cityCards : [];
  }
};
const cityStorage = {
  value: 'Москва',
  getItem: function () { return this.value; },
  setItem: function (key, value) { this.value = value; }
};

vm.runInNewContext(
  '(function cityFilterInit(){' + cityFilterBody + '})();',
  {Array, Set, document: cityDocument, localStorage: cityStorage, window: {innerWidth: 1200}}
);

assert.deepEqual(citySelect.options.map(function (option) { return option.value; }), ['', 'Казань', 'Москва']);
cityCards = cityCards.filter(function (card) { return card.city !== 'Москва'; });
documentListeners.eventdateschange();
assert.deepEqual(citySelect.options.map(function (option) { return option.value; }), ['', 'Казань']);
assert.equal(citySelect.value, '');
assert.equal(cityStorage.value, '');
