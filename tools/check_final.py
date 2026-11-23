#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""최종 검증: 홈 퀵/버튼 → 항공편 이동, 항공편 섹션, 한국어 변환(사전·API), 콘솔오류, 스크린샷."""
import asyncio, os
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))


async def main():
    console_err, page_err = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, locale='ko-KR')
        pg = await ctx.new_page()
        pg.on('console', lambda m: console_err.append(m.type + ': ' + m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: page_err.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(900)

        # 홈 퀵 첫 줄 → 항공편으로 이동
        await pg.click('#homeQuick .qrow[data-q="0"]')
        await pg.wait_for_timeout(700)
        tab = await pg.evaluate("document.querySelector('.tabbar button[aria-selected=\"true\"]').dataset.tab")
        air_top = await pg.evaluate("Math.round(document.querySelector('#air').getBoundingClientRect().top)")
        print('QUICK_AIR tab=', tab, 'airTop=', air_top)

        # 홈 카드 버튼
        await pg.click('.tabbar button[data-tab="home"]')
        await pg.wait_for_timeout(300)
        await pg.click('[data-air]')
        await pg.wait_for_timeout(700)
        print('CARD_AIR tab=', await pg.evaluate("document.querySelector('.tabbar button[aria-selected=\"true\"]').dataset.tab"),
              'airTop=', await pg.evaluate("Math.round(document.querySelector('#air').getBoundingClientRect().top)"))

        # 항공편 버튼 4개 존재 + 날짜 변경 시 URL 반영
        await pg.evaluate("document.querySelector('#flDate').value='2027-01-15'; document.querySelector('#flDate').dispatchEvent(new Event('change'))")
        await pg.wait_for_timeout(200)
        print('URLS:', await pg.eval_on_selector_all('#flBtns a', 'els => els.map(e => e.href.split("?")[0].slice(-40) + "?" + (e.href.split("?")[1]||"").slice(0,60))'))

        # 말하기 탭 안내문
        await pg.click('.tabbar button[data-tab="talk"]')
        await pg.wait_for_timeout(200)
        print('TALK_NOTE:', (await pg.inner_text('#page-talk')).count('한국어로'))

        # 마주보기: 사전 + API + 실패 시 동작
        await pg.click('#btnSplitOpen')
        await pg.wait_for_timeout(300)
        for t in ['몰라요', '얼마예요']:
            await pg.fill('#sbInput', t)
            await pg.click('#sbSend')
            await pg.wait_for_timeout(300)
            print('DICT', t, '=>', await pg.inner_text('#spJp'), '/', await pg.inner_text('#spKr'))
        await pg.fill('#sbInput', '이거 데워 주실 수 있어요?')
        await pg.click('#sbSend')
        for i in range(20):
            await pg.wait_for_timeout(500)
            if await pg.inner_text('#spJp') not in ('···',):
                break
        print('API =>', await pg.inner_text('#spJp'), '/', await pg.inner_text('#spKr'), '/', await pg.inner_text('#spKo'))
        print('SPEAK_BTN:', await pg.inner_text('#spSpeak'))
        print('CONSOLE_ERRORS:', console_err)
        print('PAGE_ERRORS:', page_err)
        await b.close()


asyncio.run(main())
