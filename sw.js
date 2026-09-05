// Версия — хеш содержимого icons/ и img/: эта статика отдаётся из кеша,
// поэтому её и нужно инвалидировать при изменении.
const CACHE_VERSION = '6214982064b4';
const STATIC_CACHE = 'onevents-static-' + CACHE_VERSION;

// Кеш страниц не версионируем: страницы идут network-first, и здесь лежит
// только офлайн-копия, которую каждый успешный ответ сети перезаписывает.
const PAGE_CACHE = 'onevents-page';

// Сколько ждём сеть на навигации, прежде чем отдать закешированную страницу
const NETWORK_TIMEOUT_MS = 3000;

var STATIC_ASSETS = [
  '/icons/site.webmanifest',
  '/icons/favicon-96x96.png',
  '/icons/favicon.svg',
  '/icons/favicon.ico',
  '/icons/apple-touch-icon.png',
  '/icons/web-app-manifest-192x192.png',
  '/icons/web-app-manifest-512x512.png'
];

function isCacheableStaticAsset(url) {
  return url.pathname.startsWith('/img/') || url.pathname.startsWith('/icons/');
}

// Удаляем из текущего кеша страницы и экспорты, сохранённые прежней версией worker.
function pruneStaticCache() {
  return caches.open(STATIC_CACHE).then(function (cache) {
    return cache.keys().then(function (requests) {
      return Promise.all(
        requests
          .filter(function (request) {
            return !isCacheableStaticAsset(new URL(request.url));
          })
          .map(function (request) {
            return cache.delete(request);
          })
      );
    });
  });
}

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(function (cache) {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    Promise.all([
      pruneStaticCache(),
      caches.keys().then(function (keys) {
        return Promise.all(
          keys
            .filter(function (key) {
              return key.startsWith('onevents-') && key !== STATIC_CACHE && key !== PAGE_CACHE;
            })
            .map(function (key) {
              return caches.delete(key);
            })
        );
      })
    ])
  );
  self.clients.claim();
});

// Навигация: сначала сеть, чтобы страница всегда была свежей.
// Кеш подставляем, только если сеть недоступна или не ответила за NETWORK_TIMEOUT_MS.
function navigateNetworkFirst(request) {
  return caches.open(PAGE_CACHE).then(function (cache) {
    return new Promise(function (resolve) {
      var settled = false;

      function settle(response) {
        if (settled || !response) {
          return;
        }
        settled = true;
        resolve(response);
      }

      var timer = setTimeout(function () {
        cache.match(request).then(settle);
      }, NETWORK_TIMEOUT_MS);

      fetch(request)
        .then(function (response) {
          clearTimeout(timer);
          if (response.ok) {
            cache.put(request, response.clone());
          }
          settle(response);
        })
        .catch(function () {
          clearTimeout(timer);
          cache.match(request).then(function (cached) {
            settle(cached || Response.error());
          });
        });
    });
  });
}

self.addEventListener('fetch', function (event) {
  var url = new URL(event.request.url);

  if (event.request.method !== 'GET') {
    return;
  }

  if (url.origin !== self.location.origin) {
    return;
  }

  if (event.request.mode === 'navigate') {
    event.respondWith(navigateNetworkFirst(event.request));
    return;
  }

  if (!isCacheableStaticAsset(url)) {
    // JSON, RSS, ICS и прочие изменяемые ресурсы браузер получает напрямую из сети.
    return;
  }

  event.respondWith(
    caches.open(STATIC_CACHE).then(function (cache) {
      return cache.match(event.request).then(function (cached) {
        return cached || fetch(event.request).then(function (response) {
          if (response.ok) {
            var clone = response.clone();
            cache.put(event.request, clone);
          }
          return response;
        });
      });
    })
  );
});
