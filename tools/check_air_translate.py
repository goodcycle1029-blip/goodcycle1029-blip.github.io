#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""japan.html 항공편 섹션 + 한국어→일본어 변환 검사 (로컬 file://)"""
import asyncio, os, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))
os.makedirs(OUT, exist_ok=True)


async def main():
    errors, pageerrors = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, locale='ko-KR')
        pg = await ctx.new_page()
        pg.on('console', lambda m: errors.append(m.type + ': ' + m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: pageerrors.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(1200)

        print('EARLY_PAGE_ERRORS:', pageerrors)
        # 1) 항공편 섹션
        await pg.click('.tabbar button[data-tab="ticket"]')
        await pg.wait_for_timeout(400)
        air = await pg.query_selector('#air')
        print('AIR_SECTION:', bool(air))
        print('BTNS:', await pg.eval_on_selector_all('#flBtns a', 'els => els.map(e => e.textContent.trim() + " | " + e.href)'))
        print('ROUTE:', await pg.inner_text('#flRoute'))
        print('CHIPS_FROM:', await pg.eval_on_selector_all('#flFrom .chip', 'els => els.map(e => e.textContent)'))
        print('CHIPS_TO:', await pg.eval_on_selector_all('#flTo .chip', 'els => els.map(e => e.textContent)'))
        # 김포→삿포로 클릭 후 안내
        await pg.click('#flFrom .chip[data-ff="gmp"]')
        await pg.click('#flTo .chip[data-ft="nrt"]')
        await pg.wait_for_timeout(200)
        print('GMP_NRT_ROUTE:', await pg.inner_text('#flRoute'))
        await pg.click('#flTo .chip[data-ft="kix"]')
        await pg.wait_for_timeout(200)
        print('GMP_KIX_BTNS:', await pg.eval_on_selector_all('#flBtns a', 'els => els.map(e => e.href)'))
        await pg.screenshot(path=os.path.join(OUT, 'japan_air_local.png'), full_page=False)
        await pg.evaluate("window.scrollTo(0,0)")
        await pg.click('#flFrom .chip[data-ff="icn"]')
        await pg.click('#flTo .chip[data-ft="nrt"]')

        # 2) 마주보기 한국어 변환
        await pg.click('#btnSplitTop')
        await pg.wait_for_timeout(300)
        for text in ['몰라요', '얼마예요']:
            await pg.fill('#sbInput', text)
            await pg.click('#sbSend')
            await pg.wait_for_timeout(250)
            print('DICT', text, '=>', await pg.inner_text('#spJp'), '/', await pg.inner_text('#spKr'), '/', await pg.inner_text('#spKo'))
        await pg.screenshot(path=os.path.join(OUT, 'japan_split_local.png'))

        # 3) 자유 문장 (API)
        await pg.fill('#sbInput', '이거 데워 주실 수 있어요?')
        await pg.click('#sbSend')
        for i in range(24):
            await pg.wait_for_timeout(500)
            jp = await pg.inner_text('#spJp')
            if jp not in ('···', 'すみません、これは何ですか？'):
                break
        print('API_FREE =>', await pg.inner_text('#spJp'), '/', await pg.inner_text('#spKr'), '/', await pg.inner_text('#spKo'))
        await pg.screenshot(path=os.path.join(OUT, 'japan_split_api_local.png'))

        print('CONSOLE_ERRORS:', errors)
        print('PAGE_ERRORS:', pageerrors)
        await b.close()


asyncio.run(main())
