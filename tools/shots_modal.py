#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""모달/마주보기 모드 화면 확인 + 오버플로 검사."""
import asyncio, os
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))

async def main():
    errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, locale='ko-KR')
        pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append('console:' + m.text) if m.type == 'error' else None)
        await pg.goto(PAGE)
        await pg.wait_for_timeout(900)

        # 문장 크게 보기
        await pg.evaluate("() => { location.hash = 'talk'; }")
        await pg.wait_for_timeout(400)
        await pg.click('#phraseList .pcard')
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=os.path.join(OUT, 'jp_modal_phrase.png'))
        clip = await pg.evaluate("""() => {
          const el = document.querySelector('#phraseFull .ov-body');
          return {scroll: el.scrollHeight, client: el.clientHeight};
        }""")
        print('phrase overlay body:', clip)
        await pg.click('#ovClose')
        await pg.wait_for_timeout(300)

        # 마주보기 모드
        await pg.click('#btnSplitTop')
        await pg.wait_for_timeout(700)
        await pg.screenshot(path=os.path.join(OUT, 'jp_modal_split.png'))
        info = await pg.evaluate("""() => {
          const q = s => document.querySelector(s);
          const box = el => el ? {sw: el.scrollWidth, cw: el.clientWidth, sh: el.scrollHeight, ch: el.clientHeight} : null;
          return {top: box(q('.split-top .split-inner')), bot: box(q('.split-bottom .split-inner')), replies: box(q('#spReplies'))};
        }""")
        print('split:', info)
        await pg.click('#spClear') if await pg.query_selector('#spClear') else None
        await pg.wait_for_timeout(200)
        await pg.click('#splitClose')
        await pg.wait_for_timeout(300)

        # 의견 모달
        await pg.evaluate("() => { location.hash = 'tips'; }")
        await pg.wait_for_timeout(300)
        await pg.evaluate("() => { const b=document.querySelector('[data-feedback-open]'); if(b){b.hidden=false;} }")
        await pg.wait_for_timeout(200)
        await pg.screenshot(path=os.path.join(OUT, 'jp_modal_fb.png'))
        print('errors:', errs[:5])
        await b.close()

asyncio.run(main())
