import asyncio, os, time
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__))
PAGE='file://'+os.path.abspath(os.path.join(HERE,'..','japan.html'))
DL=os.path.abspath(os.path.join(HERE,'..','..','..','downloads'))
stamp=time.strftime('%H%M%S')
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,has_touch=True,is_mobile=True,locale='ko-KR')
        pg=await ctx.new_page()
        await pg.goto(PAGE); await pg.wait_for_timeout(2000)
        # 캔버스에 실제로 그려진 꽃잎 수를 세기 위해 프레임 정지 후 픽셀 스캔
        out=os.path.join(DL,'japan_v2_hero_%s.png'%stamp)
        await pg.screenshot(path=out)
        print('shot',out)
        await b.close()
asyncio.run(main())
