#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""japan.html 모바일 레이아웃 검사: 탭별 가로 넘침, 마주보기 하단 입력창 화면 안 포함 여부."""
import asyncio, os
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))

TABS = ['home', 'ticket', 'route', 'talk', 'shop', 'tips']


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, locale='ko-KR')
        pg = await ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(900)
        for t in TABS:
            await pg.click(f'.tabbar button[data-tab="{t}"]')
            await pg.wait_for_timeout(250)
            ov = await pg.evaluate("""() => {
              const d = document.documentElement;
              return {sw: d.scrollWidth, cw: d.clientWidth, bodyW: document.body.scrollWidth};
            }""")
            print('TAB', t, ov)
        # 항공편 화면 상단
        await pg.click('.tabbar button[data-tab="ticket"]')
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(OUT, 'japan_air_local.png'))
        # 체크리스트 카드
        await pg.evaluate("document.querySelector('#air .card:nth-of-type(2)')||document.querySelectorAll('#air .card')[1]")
        await pg.evaluate("document.querySelectorAll('#air .card')[1].scrollIntoView({block:'start'})")
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(OUT, 'japan_air_check_local.png'))
        # 마주보기
        await pg.click('#btnSplitTop')
        await pg.wait_for_timeout(300)
        await pg.fill('#sbInput', '몰라요')
        await pg.click('#sbSend')
        await pg.wait_for_timeout(400)
        box = await pg.evaluate("""() => {
          const r = document.querySelector('.sb-input').getBoundingClientRect();
          const m = document.querySelector('#sbMic').getBoundingClientRect();
          return {inputTop: r.top, inputBottom: r.bottom, vh: window.innerHeight, micW: m.width};
        }""")
        print('SPLIT_BOX', box)
        await pg.screenshot(path=os.path.join(OUT, 'japan_split_local.png'))
        print('PAGE_ERRORS:', errs)
        await b.close()


asyncio.run(main())
