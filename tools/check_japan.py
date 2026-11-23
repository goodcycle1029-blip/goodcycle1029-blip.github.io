#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""japan.html 모바일(390x844) 검사: 콘솔오류, 글자크기, 벚꽃 캔버스, 음악 토글, 스크린샷."""
import asyncio, json, sys, os
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))
os.makedirs(OUT, exist_ok=True)

TABS = ['home', 'ticket', 'route', 'talk', 'shop', 'tips']

async def main():
    errors, pageerrors = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, locale="ko-KR")
        pg = await ctx.new_page()
        pg.on('console', lambda m: errors.append(m.type + ': ' + m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: pageerrors.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(1800)
        await pg.screenshot(path=os.path.join(OUT, 'japan_sakura_preview.png'))

        # 글자 크기 조사 (보이는 요소만)
        info = await pg.evaluate("""() => {
          const out = {min: 99, samples: [], under: []};
          const walk = (el) => {
            for (const n of el.children) {
              const cs = getComputedStyle(n);
              if (cs.display === 'none' || cs.visibility === 'hidden') continue;
              const fs = parseFloat(cs.fontSize);
              const txt = (n.childNodes.length && n.childNodes[0].nodeType === 3) ? n.childNodes[0].textContent.trim() : '';
              if (txt && txt.length > 1) {
                if (fs < out.min) out.min = fs;
                if (fs < 15) out.under.push(fs + ' | ' + n.className + ' | ' + txt.slice(0,28));
              }
              walk(n);
            }
          };
          walk(document.body);
          return out;
        }""")
        print('visible min font:', info['min'])
        print('under 15px (first 25):')
        for u in info['under'][:25]:
            print('  ', u)

        # 벚꽃 캔버스 픽셀 확인
        sak = await pg.evaluate("""() => {
          const c = document.getElementById('sakura');
          if (!c) return {err: 'no canvas'};
          const g = c.getContext('2d');
          const d = g.getImageData(0, 0, c.width, c.height).data;
          let n = 0;
          for (let i = 3; i < d.length; i += 4) if (d[i] > 8) n++;
          return {w: c.width, h: c.height, painted: n, hidden: c.hidden};
        }""")
        print('sakura:', sak)
        await pg.wait_for_timeout(600)
        sak2 = await pg.evaluate("""() => {
          const c = document.getElementById('sakura');
          const g = c.getContext('2d');
          const d = g.getImageData(0, 0, c.width, c.height).data;
          let n = 0;
          for (let i = 3; i < d.length; i += 4) if (d[i] > 8) n++;
          return n;
        }""")
        print('sakura painted after 0.6s:', sak2)

        # 탭별 콘솔 오류 확인 + 스크린샷
        shots = {}
        for t in TABS:
            await pg.evaluate("(t) => { location.hash = t; }", t)
            await pg.wait_for_timeout(500)
            path = os.path.join(OUT, 'jp_check_%s.png' % t)
            await pg.screenshot(path=path, full_page=True)
            shots[t] = path

        # 음악 버튼 토글
        await pg.evaluate("() => { location.hash = 'home'; }")
        await pg.wait_for_timeout(300)
        before = await pg.evaluate("() => document.getElementById('btnMusic').getAttribute('aria-pressed')")
        await pg.click('#btnMusic')
        await pg.wait_for_timeout(1200)
        st = await pg.evaluate("""() => ({
          pressed: document.getElementById('btnMusic').getAttribute('aria-pressed'),
          label: document.getElementById('btnMusic').getAttribute('aria-label'),
          icon: document.getElementById('btnMusic').textContent,
          toast: document.getElementById('toast').textContent,
          toastShown: document.getElementById('toast').classList.contains('show')
        })""")
        await pg.screenshot(path=os.path.join(OUT, 'jp_music_on.png'))
        await pg.click('#btnMusic')
        await pg.wait_for_timeout(700)
        off = await pg.evaluate("() => ({pressed: document.getElementById('btnMusic').getAttribute('aria-pressed'), icon: document.getElementById('btnMusic').textContent})")
        print('music before:', before, '| on:', st, '| off:', off)

        # 벚꽃 토글
        await pg.click('#btnSakura')
        await pg.wait_for_timeout(400)
        sk = await pg.evaluate("""() => {
          const c = document.getElementById('sakura');
          const g = c.getContext('2d');
          const d = g.getImageData(0, 0, c.width, c.height).data;
          let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 8) n++;
          return {pressed: document.getElementById('btnSakura').getAttribute('aria-pressed'), painted: n, hidden: c.hidden};
        }""")
        await pg.click('#btnSakura')
        await pg.wait_for_timeout(700)
        sk2 = await pg.evaluate("""() => {
          const c = document.getElementById('sakura');
          const g = c.getContext('2d');
          const d = g.getImageData(0, 0, c.width, c.height).data;
          let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 8) n++;
          return {pressed: document.getElementById('btnSakura').getAttribute('aria-pressed'), painted: n};
        }""")
        print('sakura off:', sk, '| back on:', sk2)

        # 오버플로우(가로 스크롤) 확인
        ovf = await pg.evaluate("""() => {
          const d = document.documentElement;
          const bad = [];
          document.querySelectorAll('.page.active *').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width > 0 && (r.right > 391 || r.left < -1)) bad.push(el.className + ' >> ' + (el.textContent||'').trim().slice(0,20) + ' @' + Math.round(r.left) + '/' + Math.round(r.right));
          });
          return {scrollW: d.scrollWidth, clientW: d.clientWidth, bad: bad.slice(0, 12)};
        }""")
        print('width check:', ovf)

        print('--- console errors/warnings ---')
        for e in errors:
            print('  ', e)
        print('--- page errors ---')
        for e in pageerrors:
            print('  ', e)
        await b.close()
    print('screens:', json.dumps(shots, ensure_ascii=False, indent=1))

asyncio.run(main())
