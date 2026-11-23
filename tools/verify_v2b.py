# -*- coding: utf-8 -*-
"""추가 검증: 합성 시간, 루프 이음새, <audio> 막힌 환경에서 Web Audio 대체 동작."""
import asyncio, os, wave, numpy as np
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__))
PAGE='file://'+os.path.abspath(os.path.join(HERE,'..','japan.html'))
DL=os.path.abspath(os.path.join(HERE,'..','..','..','downloads'))

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,has_touch=True,is_mobile=True,locale='ko-KR')
        pg=await ctx.new_page()
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(PAGE); await pg.wait_for_timeout(2500)
        print('build ms:', await pg.evaluate('window.__bgmMs'))
        print('stats:', await pg.evaluate('window.__bgmStats'))

        # 1) 루프 이음새: 마지막 샘플과 첫 샘플 차이
        seam = await pg.evaluate("""async () => {
          const r = await fetch(window.__bgmUrl); const buf = new ArrayBuffer;
          const ab = await r.arrayBuffer(); const d = new DataView(ab);
          const n = (ab.byteLength - 44) / 2;
          const first = d.getInt16(44, true), last = d.getInt16(44 + (n - 1) * 2, true);
          let max=0; for (let i=0;i<n;i++){ const v=Math.abs(d.getInt16(44+i*2,true)); if(v>max)max=v; }
          return { n, first, last, diff: Math.abs(first-last), max };
        }""")
        print('loop seam:', seam)

        # 2) <audio>.play() 를 막아 Web Audio 대체 엔진이 도는지
        await pg.evaluate("""() => {
          const P = HTMLMediaElement.prototype.play;
          HTMLMediaElement.prototype.play = function(){ return Promise.reject(new DOMException('blocked','NotAllowedError')); };
          window.__origPlay = P;
        }""")
        await pg.touchscreen.tap(195, 470)
        await pg.wait_for_timeout(1500)
        fb = await pg.evaluate("""() => {
          const a = document.querySelector('audio#bgm');
          return { audioPaused: a ? a.paused : null, chip: document.getElementById('btnMusic').innerText.replace(/\\s+/g,' ').trim(),
                   pressed: document.getElementById('btnMusic').getAttribute('aria-pressed') };
        }""")
        print('fallback path:', fb)
        # 대체 엔진 소리 크기(마스터 게인 값 확인용으로 컨텍스트 상태만)
        await pg.wait_for_timeout(800)
        print('page errors:', errs)
        await b.close()
asyncio.run(main())
