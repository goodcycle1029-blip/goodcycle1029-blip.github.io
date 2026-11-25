#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""대문(공식몰) 렌더 검증 — 390(폰)·1280(데스크톱) 스크린샷 + 링크/이미지 검사."""
import asyncio, os, sys, json
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('SITE_BASE', 'http://127.0.0.1:8765/')
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))

async def main():
    errors, pageerrors, failed = [], [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox'])
        for label, vw, vh, dsf, out in [
            ('mobile', 390, 844, 2, 'index_fixed_mobile.png'),
            ('desktop', 1280, 900, 1, 'index_fixed_desktop.png'),
        ]:
            ctx = await b.new_context(viewport={'width': vw, 'height': vh}, device_scale_factor=dsf, locale='ko-KR')
            pg = await ctx.new_page()
            pg.on('console', lambda m: errors.append(m.type + ': ' + m.text) if m.type == 'error' else None)
            pg.on('pageerror', lambda e: pageerrors.append(str(e)))
            pg.on('requestfailed', lambda r: failed.append(r.url))
            await pg.goto(BASE, wait_until='networkidle')
            await pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            await pg.wait_for_timeout(1400)
            await pg.evaluate("() => window.scrollTo(0, 0)")
            await pg.wait_for_timeout(600)
            await pg.screenshot(path=os.path.join(OUT, out), full_page=True)
            info = await pg.evaluate("""() => {
              const imgs = [...document.images];
              const broken = imgs.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.currentSrc || i.src);
              const links = [...document.querySelectorAll('a')].map(a => a.getAttribute('href') || '');
              const cards = document.querySelectorAll('#grid .card').length;
              const stat = document.querySelector('.stats [data-count]');
              const total = document.querySelector('[data-stat="total"]');
              return {imgs: imgs.length, broken, cards,
                      statText: stat ? stat.textContent : null,
                      totalText: total ? total.textContent : null,
                      links};
            }""")
            print('==', label, json.dumps(info, ensure_ascii=False))
            print(label, 'height', await pg.evaluate("() => document.documentElement.scrollHeight"))
            await ctx.close()
        await b.close()
    print('console errors:', errors[:8])
    print('page errors:', pageerrors[:8])
    print('failed requests:', failed[:8])

asyncio.run(main())
