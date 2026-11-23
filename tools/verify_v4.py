#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""japan.html v4 검증 — 벚꽃 글자 라벨/토글, 노래 3곡 전환·재생, 콘솔오류, 스크린샷."""
import asyncio, os, json, base64, wave, struct, math, re, sys
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
PAGE = 'file://' + os.path.join(ROOT, 'japan.html')
DL = os.path.abspath(os.path.join(ROOT, '..', '..', 'downloads'))
SHOT = os.path.join(DL, 'japan_sakura_v4_multi_bgm.png')
PC_SHOT = os.path.join(DL, 'japan_sakura_v4_pc_topbar.png')

# ---- 기대 멜로디: bgm_v4.js 원문에서 그대로 뽑아 쓴다 ----
js = open(os.path.join(HERE, 'bgm_v4.js'), encoding='utf-8').read()
def mel_of(tid):
    i = js.index("id: '%s'" % tid)
    a = js.index('mel: [', i)
    b = js.index('chords: {', a)
    return [(m.group(1), float(m.group(2))) for m in re.finditer(r"\['([A-G][#b]?-?\d)',\s*([\d.]+)\]", js[a:b])]

SEMI = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
def freq(name):
    m = re.match(r'^([A-G])([#b]?)(-?\d)$', name)
    v = (int(m.group(3)) + 1) * 12 + SEMI[m.group(1)] + (1 if m.group(2) == '#' else -1 if m.group(2) == 'b' else 0)
    return 440 * 2 ** ((v - 69) / 12)

def analyze(path, tid, beat_js):
    with wave.open(path, 'rb') as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    data = struct.unpack('<%dh' % n, raw)
    peak = max(abs(v) for v in data) / 32768.0
    rms = math.sqrt(sum(v * v for v in data) / n) / 32768.0

    def goertzel(seg, f):
        wv = 2 * math.pi * f / sr
        coeff = 2 * math.cos(wv)
        s1 = s2 = 0.0
        for v in seg:
            s0 = v / 32768.0 + coeff * s1 - s2
            s2, s1 = s1, s0
        p = s1 * s1 + s2 * s2 - coeff * s1 * s2
        return math.sqrt(max(p, 0)) / len(seg) * 2

    mel = mel_of(tid)
    win = int(0.11 * sr)
    names = sorted({m[0] for m in mel})
    hits, rows = 0, []
    t, checked = 0.0, 0
    for nm, beats in mel:
        if checked >= 10:
            break
        i = int((t + 0.03) * sr)
        seg = data[i:i + win]
        if len(seg) == win:
            sc = {x: goertzel(seg, freq(x)) for x in names}
            best = max(sc, key=sc.get)
            rows.append((round(t, 2), nm, best))
            checked += 1
            if best == nm or abs(freq(best) - freq(nm)) < 4:
                hits += 1
        t += beats * beat_js
    return {'seconds': round(n / sr, 2), 'sampleRate': sr, 'peak': round(peak, 3), 'rms': round(rms, 4),
            'melodyMatch': '%d/%d' % (hits, checked), 'melody': rows}

async def main():
    cons, errs = [], []
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, is_mobile=True, locale='ko-KR',
                                  user_agent='Mozilla/5.0 (Linux; Android 14; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36')
        pg = await ctx.new_page()
        pg.on('console', lambda m: cons.append(m.type + ': ' + m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(1200)

        # --- 라벨/레이아웃 ---
        out['labels'] = await pg.evaluate("""() => {
          const tb = document.querySelector('.topbar');
          const rect = e => { const r = e.getBoundingClientRect(); return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)}; };
          const chips = [...document.querySelectorAll('.top-chip, .track-chip')].map(e => ({
            txt: e.innerText.replace(/\\s+/g, ' ').trim(),
            aria: e.getAttribute('aria-label'),
            pressed: e.getAttribute('aria-pressed'),
            rect: rect(e), fs: getComputedStyle(e).fontSize,
            clipped: e.scrollWidth > e.clientWidth + 1
          }));
          return {topbar: rect(tb), chips,
                  docW: document.documentElement.scrollWidth, winW: window.innerWidth,
                  sakuraTxt: document.getElementById('sakuraTxt').textContent,
                  musicTxt: document.getElementById('musicTxt').textContent};
        }""")
        # --- 벚꽃 토글 ---
        def sak_px():
            return pg.evaluate("""() => {
              const c = document.getElementById('sakura');
              const g = c.getContext('2d');
              const d = g.getImageData(0, 0, c.width, c.height).data;
              let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 8) n++;
              return {painted: n, hidden: c.hidden};
            }""")
        before = await sak_px()
        await pg.click('#btnSakura')
        await pg.wait_for_timeout(500)
        off = await sak_px()
        off_txt = await pg.evaluate("() => ({txt: document.getElementById('sakuraTxt').textContent, pressed: document.getElementById('btnSakura').getAttribute('aria-pressed')})")
        await pg.screenshot(path=os.path.join(DL, 'japan_sakura_v4_off.png'))
        await pg.click('#btnSakura')
        await pg.wait_for_timeout(600)
        on = await sak_px()
        on_txt = await pg.evaluate("() => ({txt: document.getElementById('sakuraTxt').textContent, pressed: document.getElementById('btnSakura').getAttribute('aria-pressed')})")
        out['sakura'] = {'onPainted': before['painted'], 'offPainted': off['painted'], 'onAgain': on['painted'],
                         'offTxt': off_txt, 'onTxt': on_txt}

        # --- 노래 3곡 ---
        async def state():
            return await pg.evaluate("() => window.__bgmState()")
        async def grab(tid):
            b64 = await pg.evaluate("""async (tid) => {
              const us = window.__bgmUrls();
              if (!us[tid]) return null;
              const r = await fetch(us[tid]);
              const buf = new Uint8Array(await r.arrayBuffer());
              let s = ''; const CH = 0x8000;
              for (let i = 0; i < buf.length; i += CH) s += String.fromCharCode.apply(null, buf.subarray(i, i + CH));
              return btoa(s);
            }""", tid)
            if not b64:
                return None
            pth = os.path.join(DL, 'japan_bgm_v4_%s.wav' % tid)
            open(pth, 'wb').write(base64.b64decode(b64))
            return pth

        await pg.click('#btnMusic')
        await pg.wait_for_timeout(2600)
        s1 = await state()
        w1 = await grab('sakura')
        await pg.wait_for_timeout(700)
        await pg.screenshot(path=SHOT)

        await pg.click('.track-chip[data-track="moon"]')
        await pg.wait_for_timeout(2600)
        s2 = await state()
        w2 = await grab('moon')
        await pg.screenshot(path=os.path.join(DL, 'japan_sakura_v4_track_moon.png'))

        await pg.click('.track-chip[data-track="trip"]')
        await pg.wait_for_timeout(2600)
        s3 = await state()
        w3 = await grab('trip')

        # 끄기 → 다시 켜면 마지막 곡 유지되는지
        await pg.click('#btnMusic')
        await pg.wait_for_timeout(700)
        s4 = await state()
        await pg.click('#btnMusic')
        await pg.wait_for_timeout(1200)
        s5 = await state()

        beats = {'sakura': 0.35, 'moon': 0.42, 'trip': 0.30}
        out['tracks'] = [s1, s2, s3, s4, s5]
        out['wav'] = {}
        for tid, pth in (('sakura', w1), ('moon', w2), ('trip', w3)):
            if pth:
                out['wav'][tid] = analyze(pth, tid, beats[tid])
                out['wav'][tid]['path'] = pth

        # --- PC 넓은 화면 ---
        pg2 = await ctx.new_page()
        await pg2.set_viewport_size({'width': 1280, 'height': 900})
        await pg2.goto(PAGE)
        await pg2.wait_for_timeout(1500)
        await pg2.screenshot(path=PC_SHOT)
        out['pc'] = await pg2.evaluate("""() => {
          const tb = document.querySelector('.topbar').getBoundingClientRect();
          const sr = document.querySelector('#sakura').getBoundingClientRect();
          return {topbarH: Math.round(tb.height), topbarW: Math.round(tb.width), canvasX: Math.round(sr.x), canvasW: Math.round(sr.width)};
        }""")
        # --- 깨끗한 콘솔 확인(픽셀 읽기 없이 버튼만 조작하는 새 페이지) ---
        cons2, errs2 = [], []
        pg3 = await ctx.new_page()
        pg3.on('console', lambda m: cons2.append(m.type + ': ' + m.text) if m.type in ('error', 'warning') else None)
        pg3.on('pageerror', lambda e: errs2.append(str(e)))
        await pg3.goto(PAGE)
        await pg3.wait_for_timeout(1000)
        await pg3.click('#btnMusic'); await pg3.wait_for_timeout(900)
        await pg3.click('.track-chip[data-track="moon"]'); await pg3.wait_for_timeout(900)
        await pg3.click('.track-chip[data-track="trip"]'); await pg3.wait_for_timeout(900)
        await pg3.click('#btnSakura'); await pg3.wait_for_timeout(400)
        await pg3.click('#btnSakura'); await pg3.wait_for_timeout(400)
        await pg3.click('#btnMusic'); await pg3.wait_for_timeout(400)
        out['cleanConsole'] = cons2
        out['cleanPageErrors'] = errs2
        await b.close()

    out['console'] = cons
    out['pageerrors'] = errs
    out['shot'] = SHOT
    out['pcShot'] = PC_SHOT
    print(json.dumps(out, ensure_ascii=False, indent=1))

asyncio.run(main())
