import asyncio, os, json, base64, wave, struct, math
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
DL = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))
WAV = os.path.join(DL, 'japan_bgm_v3.wav')
SHOT = os.path.join(DL, 'japan_sakura_v3_calm.png')


def analyze(path):
    with wave.open(path, 'rb') as w:
        sr = w.getframerate(); n = w.getnframes(); ch = w.getnchannels(); sw = w.getsampwidth()
        raw = w.readframes(n)
    assert sw == 2 and ch == 1, (sw, ch)
    data = struct.unpack('<%dh' % n, raw)
    peak = max(abs(v) for v in data) / 32768.0
    rms = math.sqrt(sum(v * v for v in data) / n) / 32768.0

    def goertzel(seg, freq):
        wv = 2 * math.pi * freq / sr
        coeff = 2 * math.cos(wv)
        s0 = s1 = s2 = 0.0
        for v in seg:
            s0 = v / 32768.0 + coeff * s1 - s2
            s2 = s1; s1 = s0
        p = s1 * s1 + s2 * s2 - coeff * s1 * s2
        return math.sqrt(max(p, 0)) / len(seg) * 2

    # 앞 10초 구간을 0.02초 간격으로 훑어 '가장 강한 배음 주파수' 목록을 만든다
    NOTES = {'A3': 220.0, 'B3': 246.94, 'C4': 261.63, 'E4': 329.63, 'F4': 349.23,
             'A4': 440.0, 'B4': 493.88, 'C5': 523.25}
    win = int(0.12 * sr)
    found = []
    for t in (0.02, 0.37, 1.07, 1.42, 2.47, 2.82, 3.17, 3.87, 4.22, 5.27, 5.62, 5.97, 7.02,
              7.37, 8.42, 8.77, 9.12, 9.82):
        i = int(t * sr)
        seg = data[i:i + win]
        if len(seg) < win:
            continue
        scores = {name: goertzel(seg, f) for name, f in NOTES.items()}
        best = max(scores, key=scores.get)
        found.append((t, best))
    return {'seconds': round(n / sr, 3), 'sampleRate': sr, 'peak': round(peak, 3),
            'rms': round(rms, 4), 'detected': found}


async def main():
    cons, errs = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                                  has_touch=True, is_mobile=True, locale='ko-KR',
                                  user_agent='Mozilla/5.0 (Linux; Android 14; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36')
        pg = await ctx.new_page()
        pg.on('console', lambda m: cons.append({'t': m.type, 'x': m.text}) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(2500)
        await pg.screenshot(path=SHOT)

        await pg.click('#btnMusic')
        await pg.wait_for_timeout(2500)
        info = await pg.evaluate("""async () => {
          const a = document.querySelector('audio#bgm');
          const out = {stats: window.__bgmStats, buildMs: window.__bgmMs, hasUrl: !!window.__bgmUrl,
                       paused: a ? a.paused : null, dur: a ? +a.duration.toFixed(2) : null,
                       cur: a ? +a.currentTime.toFixed(2) : null, loop: a ? a.loop : null,
                       chip: document.getElementById('btnMusic').innerText.replace(/\\s+/g,' ').trim()};
          return out;
        }""")
        b64 = await pg.evaluate("""async () => {
          const r = await fetch(window.__bgmUrl);
          const buf = new Uint8Array(await r.arrayBuffer());
          let s = ''; const CH = 0x8000;
          for (let i = 0; i < buf.length; i += CH) s += String.fromCharCode.apply(null, buf.subarray(i, i + CH));
          return btoa(s);
        }""")
        with open(WAV, 'wb') as f:
            f.write(base64.b64decode(b64))
        await b.close()

    print(json.dumps({'ui': info, 'console': cons, 'pageerrors': errs,
                      'wav': analyze(WAV), 'wavPath': WAV, 'shot': SHOT},
                     ensure_ascii=False, indent=1))

asyncio.run(main())
