import asyncio, os, json
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); PAGE='file://'+os.path.abspath(os.path.join(HERE,'..','japan.html'))
DL=os.path.abspath(os.path.join(HERE,'..','..','..','downloads'))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,has_touch=True,is_mobile=True,locale='ko-KR',
            user_agent='Mozilla/5.0 (Linux; Android 14; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36')
        pg=await ctx.new_page(); await pg.goto(PAGE); await pg.wait_for_timeout(2200)
        await pg.screenshot(path=os.path.join(DL,'japan_sakura_v2_preview.png'))
        # 글자 위 벚꽃 확인용 확대 크롭(카드 영역)
        await pg.screenshot(path=os.path.join(DL,'japan_sakura_v2_zoom.png'), clip={'x':0,'y':430,'width':390,'height':300})
        await pg.touchscreen.tap(195, 470); await pg.wait_for_timeout(2000)
        await pg.screenshot(path=os.path.join(DL,'japan_sakura_v2_music_on.png'))
        st=await pg.evaluate("""() => { const a=document.querySelector('audio#bgm'); return {paused:a.paused,t:+a.currentTime.toFixed(2),v:a.volume,chip:document.getElementById('btnMusic').innerText.replace(/\\s+/g,' ').trim(),ms:window.__bgmMs}; }""")
        print(json.dumps(st, ensure_ascii=False))
        # 상단 헤더 확대(칩 모습)
        await pg.screenshot(path=os.path.join(DL,'japan_sakura_v2_chip_on.png'), clip={'x':0,'y':0,'width':390,'height':115})
        await b.close()
asyncio.run(main())
