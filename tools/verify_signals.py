import asyncio, os, json, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DL = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))
URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765/company.html'
TAG = sys.argv[2] if len(sys.argv) > 2 else 'local'

async def main():
    errs, perrs = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, is_mobile=True, locale='ko-KR')
        pg = await ctx.new_page()
        pg.on('console', lambda m: errs.append(m.type + ': ' + m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: perrs.append(str(e)))
        await pg.goto(URL, wait_until='load')
        await pg.wait_for_timeout(1800)
        # 조직도 탭
        await pg.click('#t1')
        await pg.wait_for_timeout(1200)
        info = await pg.evaluate("""() => {
          const out=[];
          document.querySelectorAll('#orgTree .tnode').forEach(n=>{
            const b=n.querySelector('b');
            const led=n.querySelector('.led');
            const line=n.querySelector('.tlive .lw');
            out.push({
              name:b?b.textContent:null,
              cls:n.className,
              led:led?getComputedStyle(led).animationName+'/'+getComputedStyle(led).animationDuration:null,
              line:line?line.textContent:null,
              box:n.getBoundingClientRect().height
            });
          });
          const g=document.querySelector('.siglegend');
          return {nodes:out, legend:g?g.textContent.replace(/\\s+/g,' ').trim():null, wide:document.getElementById('orgTree').classList.contains('wide')};
        }""")
        print(json.dumps(info, ensure_ascii=False, indent=1))
        await pg.screenshot(path=os.path.join(DL, 'sig_%s_top.png' % TAG))
        await pg.evaluate("window.scrollTo(0, document.getElementById('orgTree').getBoundingClientRect().top + window.scrollY - 60)")
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=os.path.join(DL, 'sig_%s_tree1.png' % TAG))
        await pg.evaluate("window.scrollBy(0, 760)")
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=os.path.join(DL, 'sig_%s_tree2.png' % TAG))
        # 탭0 직원 카드
        await pg.click('#t0')
        await pg.wait_for_timeout(900)
        await pg.evaluate("window.scrollTo(0, document.getElementById('stStaff').getBoundingClientRect().top + window.scrollY - 80)")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=os.path.join(DL, 'sig_%s_staff.png' % TAG))
        print('console errors:', errs[:6])
        print('page errors:', perrs[:6])
        await b.close()

asyncio.run(main())
