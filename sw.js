/* =========================================================================
   재팬마트박스 공식몰 서비스워커
   -------------------------------------------------------------------------
   · 홈 화면에 추가한 앱이 인터넷이 잠깐 끊겨도 마지막으로 연 화면을 열어 줍니다.
   · 화면(HTML)·이미지는 항상 네트워크를 먼저 확인해 새 버전을 받고, 실패할 때만 저장본을 씁니다.
   · 실시간 현황(status.json)은 캐시하지 않고 그대로 통과시킵니다.
   ========================================================================= */
var CACHE = 'japanmartbox-shop-v2';
var CORE = [
  './index.html',
  './assets/hero_jmb_v3.jpg',
  './assets/band_atelier.jpg',
  './assets/banner_jmb_v1.jpg',
  './manifest-portal.json',
  './icon-portal-192.png',
  './icon-portal-512.png'
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
  if (url.origin !== self.location.origin) return;   /* 외부 링크(마켓)는 그대로 통과 */

  /* 실시간 현황(status.json)은 항상 네트워크에서 새로 받고 캐시에 쌓지 않습니다 */
  if (url.pathname.indexOf('/status.json') >= 0 || url.search.indexOf('_=') >= 0) {
    event.respondWith(fetch(req, { cache: 'no-store' }).catch(function () {
      return new Response('{"offline":true}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }));
    return;
  }

  /* 화면·이미지: 네트워크 우선 → 실패하면 저장본 */
  event.respondWith(
    fetch(req).then(function (res) {
      if (res && res.ok) {
        var copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
      }
      return res;
    }).catch(function () {
      return caches.match(req).then(function (hit) {
        if (hit) return hit;
        if (req.mode === 'navigate') return caches.match('./index.html');
        return new Response('', { status: 504 });
      });
    })
  );
});
