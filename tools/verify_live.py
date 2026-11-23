#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""라이브(github.io) 검증: 항공편 섹션·한국어→일본어 변환·콘솔오류·모바일 레이아웃 + 스크린샷."""
import asyncio, os
from playwright.async_api import async_playwright

URL = 'https://goodcycle1029-blip.github.io/japan.html'
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'downloads'))


async def main():
    console_err, page_err = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, locale='ko-KR')
        pg = await ctx.new_page()
        pg.on('console', lambda m: console_err.append(m.type + ': ' + m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: page_err.append(str(e)))
        r = await pg.goto(URL, wait_until='domcontentloaded')
        print('HTTP', r.status if r else None)
        await pg.wait_for_timeout(1500)

        # 항공편
        await pg.click('#homeQuick .qrow[data-q="0"]')
        await pg.wait_for_timeout(800)
        print('AIR_VISIBLE:', await pg.is_visible('#air'))
        print('HEAD:', await pg.inner_text('#air h2'))
        print('LINKS:', await pg.eval_on_selector_all('#flBtns a', 'els => els.map(e => e.textContent.trim())'))
        print('DEST:', await pg.eval_on_selector_all('#flTo .chip', 'els => els.map(e => e.textContent.trim())'))
        # 두 번째 항공편 카드로 스크롤해 체크리스트까지 한 장에
        await pg.evaluate("document.querySelector('#air').scrollIntoView({block:'start'})")
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(OUT, '일본여행앱_항공편_번역개선.png'))
        await pg.evaluate("window.scrollBy(0,760)")
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(OUT, '일본여행앱_항공편_체크리스트.png'))

        # 말하기
        await pg.click('.tabbar button[data-tab="talk"]')
        await pg.wait_for_timeout(300)
        await pg.click('#btnSplitOpen')
        await pg.wait_for_timeout(400)
        for t in ['몰라요', '얼마예요']:
            await pg.fill('#sbInput', t)
            await pg.click('#sbSend')
            await pg.wait_for_timeout(350)
            print('KO', t, '=>', await pg.inner_text('#spJp'), '/', await pg.inner_text('#spKr'), '/', await pg.inner_text('#spKo'))
        await pg.screenshot(path=os.path.join(OUT, '일본여행앱_한국어번역.png'))
        # 자유 문장
        await pg.fill('#sbInput', '이거 데워 주실 수 있어요?')
        await pg.click('#sbSend')
        for _ in range(20):
            await pg.wait_for_timeout(500)
            if await pg.inner_text('#spJp') != '···':
                break
        print('FREE =>', await pg.inner_text('#spJp'), '/', await pg.inner_text('#spKr'))
        await pg.screenshot(path=os.path.join(OUT, '일본여행앱_자유문장번역.png'))

        # 일본어 직접 입력은 그대로
        await pg.fill('#sbInput', 'ありがとうございます')
        await pg.click('#sbSend')
        await pg.wait_for_timeout(300)
        print('JA_DIRECT =>', await pg.inner_text('#spJp'), '/', await pg.inner_text('#spKr'))

        # 가로 넘침
        print('OVERFLOW:', await pg.evaluate("({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth})"))
        print('CONSOLE_ERRORS:', console_err)
        print('PAGE_ERRORS:', page_err)
        await b.close()


asyncio.run(main())
