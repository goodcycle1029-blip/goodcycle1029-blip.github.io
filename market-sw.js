/* =========================================================================
   내 마켓 현황판 전용 서비스워커
   -------------------------------------------------------------------------
   · 이 앱(market-board)만 담당합니다. 범위(scope)를 좁혀 두어
     기존 게임·회사 화면용 sw.js 와 서로 덮어쓰지 않습니다.
   · 화면은 인터넷을 먼저 확인해 새 버전을 받고, 실패하면 저장본을 씁니다.
   · 외부 주소(미니게임 링크 등)는 가로채지 않습니다.
   ========================================================================= */
var CACHE = 'market-board-v4';
var CORE = [
  './market-board.html',
  './market-manifest.json',
  './icon-market.svg',
  './icon-market-192.png',
  './icon-market-512.png',
  './icon-market-maskable-512.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return Promise.all(CORE.map(function (url) {
        return cache.add(new Request(url, { cache: 'reload' })).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (key) {
        if (key.indexOf('market-board-') === 0 && key !== CACHE) return caches.delete(key);
        return null;
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function isMine(url) {
  var p = url.pathname;
  return p.indexOf('/market-board') === 0 ||
    p.indexOf('/market-manifest') === 0 ||
    p.indexOf('/icon-market') === 0;
}

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;
  var url;
  try { url = new URL(req.url); } catch (e) { return; }
  if (url.origin !== self.location.origin) return;
  if (!isMine(url)) return;

  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put('./market-board.html', copy); }).catch(function () {});
        return res;
      }).catch(function () {
        return caches.match('./market-board.html').then(function (hit) {
          return hit || caches.match(req);
        });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(function (hit) {
      if (hit) return hit;
      return fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
        }
        return res;
      });
    })
  );
});

self.addEventListener('message', function (event) {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
