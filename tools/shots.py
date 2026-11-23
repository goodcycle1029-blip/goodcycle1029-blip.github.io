#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""japan.html 모바일(390x844) 화면 확인용 뷰포트 스크린샷 + 기본 검사."""
import asyncio, os, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))
os.makedirs(OUT, exist_ok=True)
TABS = sys.argv[1].split(',') if len(sys.argv) > 1 else ['home', 'ticket', 'route', 'talk', 'shop', 'tips']

async def main():
    errors, pageerrors = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, locale='ko-KR')
        pg = await ctx.new_page()
        pg.on('console', lambda m: errors.append(m.type + ': ' + m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: pageerrors.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(1200)
        for t in TABS:
            await pg.evaluate("(t) => { location.hash = t; window.scrollTo(0,0); }", t)
            await pg.wait_for_timeout(600)
            h = await pg.evaluate("() => document.documentElement.scrollHeight")
            i = 0
            y = 0
            while y < h and i < 6:
                await pg.evaluate("(y) => window.scrollTo(0, y)", y)
                await pg.wait_for_timeout(350)
                await pg.screenshot(path=os.path.join(OUT, 'jp_v_%s_%d.png' % (t, i)))
                y += 760
                i += 1
                h = await pg.evaluate("() => document.documentElement.scrollHeight")
            print(t, 'height', h, 'shots', i)
        print('errors:', errors[:5], 'pageerrors:', pageerrors[:5])
        await b.close()

asyncio.run(main())
