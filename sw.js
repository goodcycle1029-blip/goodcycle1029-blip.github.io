/* =========================================================================
   미니게임 PWA 서비스워커 (원터치 타워 · 느긋한 숫자블록 · 30초 풍선 톡톡 공용)
   -------------------------------------------------------------------------
   · 홈 화면에 추가한 앱이 인터넷이 잠깐 끊겨도 마지막으로 연 화면을 열어 줍니다.
   · 화면(HTML)은 항상 네트워크를 먼저 확인해 새 버전을 받고, 실패할 때만 저장본을 씁니다.
   · 랭킹 서버(구글 시트·Apps Script) 같은 외부 주소는 건드리지 않습니다.
   ========================================================================= */
var CACHE = 'minigame-v19';
var CORE = [
  './index.html',
  './company.html',
  './company-manifest.json',
  './icon-company-192.png',
  './icon-company-512.png',
  './japan.html',
  './tower.html',
  './drop.html',
  './pop.html',
  './manifest-portal.json',
  './icon-portal-192.png',
  './icon-portal-512.png',
  './manifest-tower.json',
  './manifest-drop.json',
  './manifest-pop.json',
  './icon-tower-192.png',
  './icon-tower-512.png',
  './icon-drop-192.png',
  './icon-drop-512.png',
  './icon-pop-192.png',
  './icon-pop-512.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      /* 파일 하나가 없어도 설치는 되도록 개별적으로 담습니다 */
      return Promise.all(CORE.map(function (url) {
        return cache.add(new Request(url, { cache: 'reload' })).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        return k === CACHE ? null : caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;

  var url;
  try { url = new URL(req.url); } catch (e) { return; }
  if (url.origin !== self.location.origin) return;   /* 외부 API(랭킹 서버)는 그대로 통과 */

  var accept = req.headers.get('accept') || '';
  var isDoc = req.mode === 'navigate' || accept.indexOf('text/html') >= 0;

  /* 실시간 현황(status.json)은 항상 네트워크에서 새로 받고 캐시에 쌓지 않습니다 */
  if (url.pathname.indexOf('/status.json') >= 0 || url.search.indexOf('_=') >= 0) {
    event.respondWith(fetch(req, { cache: 'no-store' }).catch(function () {
      return new Response('{"offline":true}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }));
    return;
  }

  if (isDoc) {
    /* 화면: 네트워크 우선 → 실패하면 저장본 */
    event.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
        }
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || caches.match('./tower.html');
        });
      })
    );
    return;
  }

  /* 아이콘·매니페스트 등: 저장본 우선 → 없으면 받아서 저장 */
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
