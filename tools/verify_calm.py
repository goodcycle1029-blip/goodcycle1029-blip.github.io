import asyncio, os, json, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
DL = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))
os.makedirs(DL, exist_ok=True)

MASK_JS = """() => {
  const cv = document.getElementById('sakura');
  const ctx = cv.getContext('2d');
  const w = cv.width, h = cv.height;
  const d = ctx.getImageData(0, 0, w, h).data;
  // 4배 다운샘플한 알파 마스크
  const sw = Math.floor(w/4), sh = Math.floor(h/4);
  const m = new Uint8Array(sw*sh);
  for (let y=0; y<sh; y++) for (let x=0; x<sw; x++) {
    const a = d[((y*4)*w + (x*4))*4 + 3];
    m[y*sw+x] = a > 24 ? 1 : 0;
  }
  return {w: sw, h: sh, px: Array.from(m), cw: w, ch: h};
}"""

SAMPLE_JS = """() => {
  const cv = document.getElementById('sakura');
  const ctx = cv.getContext('2d');
  // 다음 프레임에서 위치를 읽기 위해 frame 훅 대신, 현재 캔버스를 200ms 간격으로 두 번 읽어 이동량을 계산
  const d = ctx.getImageData(0,0,cv.width,cv.height).data;
  let sumY = 0, n = 0, minY = 1e9, maxY = -1;
  for (let y=0; y<cv.height; y+=2) for (let x=0; x<cv.width; x+=2) {
    const a = d[(y*cv.width + x)*4 + 3];
    if (a > 40) { sumY += y; n++; if (y<minY) minY=y; if (y>maxY) maxY=y; }
  }
  return {n, avgY: n? sumY/n : 0, minY, maxY};
}"""


def count_blobs(res):
    w, h, px = res['w'], res['h'], res['px']
    seen = [False] * (w * h)
    blobs = 0
    sizes = []
    for i in range(w * h):
        if px[i] and not seen[i]:
            blobs += 1
            stack = [i]
            seen[i] = True
            size = 0
            while stack:
                c = stack.pop()
                size += 1
                cy, cx = divmod(c, w)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w:
                            j = ny * w + nx
                            if px[j] and not seen[j]:
                                seen[j] = True
                                stack.append(j)
            if size >= 3:
                sizes.append(size)
    return blobs, sorted(sizes, reverse=True)[:5]


async def main():
    console, errors = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, is_mobile=True, locale='ko-KR',
                                  user_agent='Mozilla/5.0 (Linux; Android 14; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36')
        pg = await ctx.new_page()
        pg.on('console', lambda m: (console.append({'type': m.type, 'text': m.text}) if m.type in ('error', 'warning') else None))
        pg.on('pageerror', lambda e: errors.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(2500)
        shot = os.path.join(DL, 'japan_sakura_v3_calm.png')
        await pg.screenshot(path=shot)

        m1 = await pg.evaluate(MASK_JS)
        blobs, sizes = count_blobs(m1)

        s1 = await pg.evaluate(SAMPLE_JS)
        await pg.wait_for_timeout(1500)
        s2 = await pg.evaluate(SAMPLE_JS)

        # 넓은 PC 화면에서도 앱 폭(480px) 안에서만 나는지 확인
        await pg.set_viewport_size({'width': 1280, 'height': 860})
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=os.path.join(DL, 'japan_sakura_v3_calm_pc.png'))
        cw = await pg.evaluate("() => { const c=document.getElementById('sakura'); const r=c.getBoundingClientRect(); return {left:r.left,width:r.width,vw:innerWidth}; }")

        print(json.dumps({
            'viewport': '390x844 @2x',
            'blobs': blobs,
            'blobSizes': sizes,
            'sample1': s1,
            'sample2': s2,
            'pc_canvas': cw,
            'console': console,
            'pageerrors': errors,
            'screenshot': shot,
        }, ensure_ascii=False, indent=1))
        await b.close()

asyncio.run(main())
