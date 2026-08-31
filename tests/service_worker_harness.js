const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const ORIGIN = 'https://onevents.ru';
const STATIC_CACHE = 'onevents-static-test';
const PAGE_CACHE = 'onevents-page';
const listeners = {};
const deletedCaches = [];
const fetchCalls = [];

function response(name) {
  return {
    name: name,
    ok: true,
    clone: function () { return this; }
  };
}

function request(path, mode) {
  return {
    url: path.startsWith('http') ? path : ORIGIN + path,
    method: 'GET',
    mode: mode || 'cors'
  };
}

function makeCache(initialRequests) {
  return {
    addedAssets: [],
    deleted: [],
    matches: [],
    puts: [],
    responses: new Map(),
    addAll: function (assets) {
      this.addedAssets = assets;
      return Promise.resolve();
    },
    keys: function () { return Promise.resolve(initialRequests || []); },
    match: function (cachedRequest) {
      this.matches.push(cachedRequest.url);
      return Promise.resolve(this.responses.get(cachedRequest.url));
    },
    put: function (cachedRequest, cachedResponse) {
      this.puts.push([cachedRequest.url, cachedResponse.name]);
      return Promise.resolve();
    },
    delete: function (cachedRequest) {
      this.deleted.push(cachedRequest.url);
      return Promise.resolve(true);
    }
  };
}

const staticCache = makeCache([
  request('/'),
  request('/json/events.json'),
  request('/img/events/logo.png')
]);
const pageCache = makeCache();

global.self = {
  location: {origin: ORIGIN},
  clients: {claim: function () { return Promise.resolve(); }},
  skipWaiting: function () {},
  addEventListener: function (name, handler) { listeners[name] = handler; }
};

global.caches = {
  open: function (name) {
    return Promise.resolve(name === PAGE_CACHE ? pageCache : staticCache);
  },
  keys: function () {
    return Promise.resolve([STATIC_CACHE, PAGE_CACHE, 'onevents-static-old', 'third-party-cache']);
  },
  delete: function (name) {
    deletedCaches.push(name);
    return Promise.resolve(true);
  },
  match: function () {
    throw new Error('Static requests must be matched only in STATIC_CACHE');
  }
};

global.fetch = function (networkRequest) {
  fetchCalls.push(networkRequest.url);
  if (networkRequest.url === ORIGIN + '/offline/') {
    return Promise.reject(new Error('offline'));
  }
  return Promise.resolve(response('network'));
};

const source = fs.readFileSync('web/sw.js', 'utf8').replace('{{ cache_version }}', 'test');
vm.runInThisContext(source, {filename: 'web/sw.js'});

async function dispatchFetch(fetchRequest) {
  let responsePromise;
  listeners.fetch({
    request: fetchRequest,
    respondWith: function (promise) { responsePromise = Promise.resolve(promise); }
  });
  return responsePromise;
}

async function main() {
  let installation;
  listeners.install({waitUntil: function (promise) { installation = promise; }});
  await installation;
  assert.equal(staticCache.addedAssets.includes('/'), false);
  assert.equal(staticCache.addedAssets.every(function (asset) { return asset.startsWith('/icons/'); }), true);

  assert.equal(await dispatchFetch(request('/json/events.json')), undefined);
  assert.equal(await dispatchFetch(request('/rss/rss.xml')), undefined);
  assert.equal(await dispatchFetch(request('/calendar/all.ics')), undefined);
  assert.equal(await dispatchFetch(request('https://example.com/img/logo.png')), undefined);
  assert.deepEqual(fetchCalls, []);

  staticCache.responses.set(ORIGIN + '/icons/favicon.svg', response('cached-icon'));
  const cachedIconResult = await dispatchFetch(request('/icons/favicon.svg'));
  assert.equal(cachedIconResult.name, 'cached-icon');
  assert.deepEqual(fetchCalls, []);

  const imageResult = await dispatchFetch(request('/img/events/logo.png'));
  assert.equal(imageResult.name, 'network');
  assert.deepEqual(staticCache.matches, [ORIGIN + '/icons/favicon.svg', ORIGIN + '/img/events/logo.png']);
  assert.deepEqual(staticCache.puts, [[ORIGIN + '/img/events/logo.png', 'network']]);

  const navigationResult = await dispatchFetch(request('/', 'navigate'));
  assert.equal(navigationResult.name, 'network');
  assert.deepEqual(pageCache.matches, []);
  assert.deepEqual(pageCache.puts, [[ORIGIN + '/', 'network']]);

  pageCache.responses.set(ORIGIN + '/offline/', response('cached-page'));
  const offlineResult = await dispatchFetch(request('/offline/', 'navigate'));
  assert.equal(offlineResult.name, 'cached-page');
  assert.equal(pageCache.matches.includes(ORIGIN + '/offline/'), true);

  let activation;
  listeners.activate({waitUntil: function (promise) { activation = promise; }});
  await activation;
  assert.deepEqual(deletedCaches, ['onevents-static-old']);
  assert.deepEqual(staticCache.deleted, [ORIGIN + '/', ORIGIN + '/json/events.json']);
}

main().catch(function (error) {
  console.error(error);
  process.exit(1);
});
