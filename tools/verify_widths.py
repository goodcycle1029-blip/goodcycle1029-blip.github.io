import asyncio, os
from playwright.async_api import async_playwright
HERE=os.path.dirname(os.path.abspath(__file__)); PAGE='file://'+os.path.abspath(os.path.join(HERE,'..','japan.html'))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for w,h in [(320,568),(360,740),(390,844),(430,932)]:
            ctx=await b.new_context(viewport={'width':w,'height':h},device_scale_factor=2,has_touch=True,is_mobile=True,locale='ko-KR')
            pg=await ctx.new_page(); await pg.goto(PAGE); await pg.wait_for_timeout(1200)
            r=await pg.evaluate("""() => {
              const doc=document.documentElement, chip=document.getElementById('btnMusic');
              const cr=chip.getBoundingClientRect();
              const over=[...document.querySelectorAll('body *')].filter(e=>{const b=e.getBoundingClientRect();return b.width>0 && (b.right>doc.clientWidth+1 || b.left<-1);}).slice(0,6).map(e=>e.tagName+'.'+(e.className||'')+':'+Math.round(e.getBoundingClientRect().right));
              return {sw:doc.scrollWidth, cw:doc.clientWidth, chipW:Math.round(cr.width), chipH:Math.round(cr.height), headerH:Math.round(document.querySelector('.topbar').getBoundingClientRect().height), over};
            }""")
            print(w, h, r)
            await ctx.close()
        await b.close()
asyncio.run(main())
