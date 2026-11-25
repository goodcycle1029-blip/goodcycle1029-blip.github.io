#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""대표 6종 교체 검증 — 폰(390)·데스크톱(1280) 스크린샷 + 카드/이미지/링크 점검."""
import asyncio, os, json
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get('SITE_BASE') or 'file://' + os.path.abspath(os.path.join(HERE, '..', 'index.html'))
EXE = os.environ.get('CHROME_EXE') or '/workspace/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome'
OUT = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=EXE, args=['--no-sandbox', '--disable-dev-shm-usage'])
        for label, vw, vh, dsf in [('mobile', 390, 844, 2), ('desktop', 1280, 900, 1)]:
            ctx = await b.new_context(viewport={'width': vw, 'height': vh},
                                      device_scale_factor=dsf, locale='ko-KR',
                                      has_touch=(label == 'mobile'), is_mobile=(label == 'mobile'))
            pg = await ctx.new_page()
            await pg.goto(BASE, wait_until='networkidle')
            await pg.evaluate("() => window.scrollTo(0, document.getElementById('selected').offsetTop)")
            await pg.wait_for_timeout(900)
            sec = pg.locator('#selected')
            await sec.screenshot(path=os.path.join(OUT, f'picks_{label}.png'))
            await pg.screenshot(path=os.path.join(OUT, f'picks_{label}_full.png'), full_page=True)
            info = await pg.evaluate("""() => {
              const imgs=[...document.querySelectorAll('#selected img')];
              const broken=imgs.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.currentSrc||i.src);
              const cards=[...document.querySelectorAll('#selected .card')].map(c=>({
                nm:c.querySelector('.nm')?.textContent.trim(),
                pr:c.querySelector('.pr')?.textContent.trim(),
                links:[...c.querySelectorAll('a')].map(a=>a.href)}));
              const doc=document.documentElement;
              return {broken, cards, overflow: doc.scrollWidth-doc.clientWidth,
                      imgs: imgs.map(i=>[i.getAttribute('src'), i.naturalWidth, i.naturalHeight])};
            }""")
            print(label, json.dumps(info, ensure_ascii=False, indent=1))
            await ctx.close()
        await b.close()

asyncio.run(main())
