#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""japan.html v2 검증: 벚꽃 선명도(픽셀 측정) + 음악 실제 재생(<audio>) + WAV 합성 음질."""
import asyncio, base64, json, os, sys, wave, io
import numpy as np
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = 'file://' + os.path.abspath(os.path.join(HERE, '..', 'japan.html'))
DL = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'downloads'))
os.makedirs(DL, exist_ok=True)

STATE = {}


async def main():
    errs, pageerrs, warns = [], [], []
    async with async_playwright() as p:
        b = await p.chromium.launch()          # 자동재생 예외 플래그 없이(실제 모바일과 같은 조건)
        ctx = await b.new_context(
            viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True,
            is_mobile=True, locale='ko-KR',
            user_agent='Mozilla/5.0 (Linux; Android 14; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36')
        pg = await ctx.new_page()
        pg.on('console', lambda m: (errs.append(m.text) if m.type == 'error' else (warns.append(m.text) if m.type == 'warning' else None)))
        pg.on('pageerror', lambda e: pageerrs.append(str(e)))
        await pg.goto(PAGE)
        await pg.wait_for_timeout(2200)

        # ---- 1) 벚꽃 선명도: 캔버스 픽셀 측정 + 스크린샷 ----
        await pg.screenshot(path=os.path.join(DL, 'japan_sakura_v2_preview.png'))
        sak = await pg.evaluate("""() => {
          const c = document.getElementById('sakura');
          const g = c.getContext('2d');
          const d = g.getImageData(0, 0, c.width, c.height).data;
          let painted = 0, vivid = 0, strong = 0, rSum = 0, gSum = 0, bSum = 0;
          for (let i = 0; i < d.length; i += 4) {
            const a = d[i + 3];
            if (a > 20) {
              painted++;
              rSum += d[i]; gSum += d[i + 1]; bSum += d[i + 2];
              if (a > 190) strong++;
              if (d[i] > 200 && d[i + 1] < 175 && a > 190) vivid++;   // 진한 핑크
            }
          }
          return { w: c.width, h: c.height, painted, strong, vivid,
                   avg: painted ? [Math.round(rSum/painted), Math.round(gSum/painted), Math.round(bSum/painted)] : null };
        }""")
        print('sakura:', json.dumps(sak, ensure_ascii=False))

        # 꽃잎 개수(스크립트 상태)
        n = await pg.evaluate("""() => {
          // 캔버스에 그려진 꽃잎 수는 직접 못 읽으니, 화면상 존재하는 petal 수를 추정:
          // 대신 aria/버튼 상태와 캔버스 크기만 확인
          const c = document.getElementById('sakura');
          return { hidden: c.hidden, cssW: c.clientWidth, cssH: c.clientHeight };
        }""")
        print('canvas:', json.dumps(n, ensure_ascii=False))

        # ---- 2) 칩 UI 상태(시작 전) ----
        chip0 = await pg.evaluate("""() => {
          const b = document.getElementById('btnMusic');
          const r = b.getBoundingClientRect();
          return { txt: b.innerText.replace(/\\s+/g,' ').trim(), pressed: b.getAttribute('aria-pressed'),
                   w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top),
                   bg: getComputedStyle(b).backgroundImage.slice(0, 40), overflow: document.documentElement.scrollWidth };
        }""")
        print('chip(before):', json.dumps(chip0, ensure_ascii=False))

        # ---- 3) 화면 아무 곳(빈 영역) 첫 터치 → 음악 자동 시작 ----
        await pg.touchscreen.tap(195, 470)
        await pg.wait_for_timeout(1600)
        st1 = await pg.evaluate("""() => {
          const a = document.querySelector('audio#bgm');
          return { has: !!a, paused: a ? a.paused : null, t: a ? +a.currentTime.toFixed(2) : null,
                   dur: a && isFinite(a.duration) ? +a.duration.toFixed(2) : null, vol: a ? a.volume : null,
                   loop: a ? a.loop : null, playsinline: a ? a.getAttribute('playsinline') : null,
                   ready: a ? a.readyState : null, err: a && a.error ? a.error.code : null,
                   chip: document.getElementById('btnMusic').innerText.replace(/\\s+/g,' ').trim(),
                   pressed: document.getElementById('btnMusic').getAttribute('aria-pressed'),
                   stats: window.__bgmStats || null, ls: localStorage.getItem('jp_music_on') };
        }""")
        print('after first tap:', json.dumps(st1, ensure_ascii=False))
        await pg.screenshot(path=os.path.join(DL, 'japan_sakura_v2_music_on.png'))

        await pg.wait_for_timeout(2000)
        st2 = await pg.evaluate("""() => { const a = document.querySelector('audio#bgm'); return { paused: a.paused, t: +a.currentTime.toFixed(2) }; }""")
        print('after +2s:', json.dumps(st2, ensure_ascii=False))

        # ---- 4) WAV Blob 을 파일로 꺼내 실제 소리 분석 ----
        b64 = await pg.evaluate("""async () => {
          if (!window.__bgmUrl) return null;
          const r = await fetch(window.__bgmUrl);
          const buf = new Uint8Array(await r.arrayBuffer());
          let s = '';
          for (let i = 0; i < buf.length; i += 8192) s += String.fromCharCode.apply(null, buf.subarray(i, i + 8192));
          return btoa(s);
        }""")
        if b64:
            raw = base64.b64decode(b64)
            wp = os.path.join(DL, 'japan_bgm_v2.wav')
            open(wp, 'wb').write(raw)
            wf = wave.open(wp, 'rb')
            print('wav file:', wp, os.path.getsize(wp), 'bytes', wf.getframerate(), 'Hz',
                  wf.getnchannels(), 'ch', wf.getsampwidth() * 8, 'bit', round(wf.getnframes() / wf.getframerate(), 2), 'sec')
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype='<i2').astype(np.float32) / 32768.0
            print('wav peak %.3f rms %.3f' % (float(np.abs(data).max()), float(np.sqrt((data ** 2).mean()))))
            sr = wf.getframerate()
            # 초당 RMS (조용한 구간 없는지)
            per = [round(float(np.sqrt((data[i:i + sr] ** 2).mean())), 3) for i in range(0, len(data) - sr + 1, sr)]
            print('rms per second:', per)
            # 주요 음(스펙트럼 피크 상위 주파수, 처음 4초)
            seg = data[:sr * 4]
            sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
            fr = np.fft.rfftfreq(len(seg), 1 / sr)
            idx = np.argsort(sp)[-14:][::-1]
            peaks = sorted(set(int(round(fr[i])) for i in idx if fr[i] > 200))
            print('spectral peaks(Hz):', peaks[:12])
        else:
            print('!! window.__bgmUrl 없음 — WAV 합성 실패')
            b64 = None

        # ---- 5) 칩으로 끄기 → 저장/중지 ----
        await pg.click('#btnMusic')
        await pg.wait_for_timeout(700)
        st3 = await pg.evaluate("""() => { const a = document.querySelector('audio#bgm');
          return { paused: a.paused, t: +a.currentTime.toFixed(2), chip: document.getElementById('btnMusic').innerText.replace(/\\s+/g,' ').trim(),
                   pressed: document.getElementById('btnMusic').getAttribute('aria-pressed'), ls: localStorage.getItem('jp_music_on') }; }""")
        print('after chip off:', json.dumps(st3, ensure_ascii=False))

        # ---- 6) 다시 칩으로 켜기 ----
        await pg.click('#btnMusic')
        await pg.wait_for_timeout(1200)
        st4 = await pg.evaluate("""() => { const a = document.querySelector('audio#bgm');
          return { paused: a.paused, t: +a.currentTime.toFixed(2), chip: document.getElementById('btnMusic').innerText.replace(/\\s+/g,' ').trim(), ls: localStorage.getItem('jp_music_on') }; }""")
        print('after chip on:', json.dumps(st4, ensure_ascii=False))

        # ---- 7) "껐다" 기억 확인: 끈 상태로 새로 열면 자동 재생 안 함 ----
        await pg.click('#btnMusic')      # 끄기
        await pg.wait_for_timeout(400)
        await pg.reload()
        await pg.wait_for_timeout(1500)
        await pg.touchscreen.tap(195, 470)
        await pg.wait_for_timeout(1200)
        st5 = await pg.evaluate("""() => { const a = document.querySelector('audio#bgm');
          return { has: !!a, paused: a ? a.paused : null, t: a ? +a.currentTime.toFixed(2) : null,
                   chip: document.getElementById('btnMusic').innerText.replace(/\\s+/g,' ').trim(), ls: localStorage.getItem('jp_music_on') }; }""")
        print('after reload+ tap (music was off):', json.dumps(st5, ensure_ascii=False))

        # ---- 8) 벚꽃 토글 + 다른 탭 확인 ----
        await pg.click('#btnSakura')
        await pg.wait_for_timeout(400)
        sak_off = await pg.evaluate("""() => { const c = document.getElementById('sakura'); const g = c.getContext('2d');
          const d = g.getImageData(0,0,c.width,c.height).data; let n=0; for (let i=3;i<d.length;i+=4) if (d[i]>20) n++; return n; }""")
        print('sakura pixels when off:', sak_off)
        await pg.click('#btnSakura')
        await pg.wait_for_timeout(600)

        # WAV 합성 시간 측정(모바일 체감)
        t_gen = await pg.evaluate("""() => { const t0 = performance.now(); return { ms: 0, stats: window.__bgmStats }; }""")
        print('bgm stats:', json.dumps(t_gen['stats'], ensure_ascii=False))

        # 레이아웃
        lay = await pg.evaluate("""() => ({ scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
            headerH: Math.round(document.querySelector('.topbar').getBoundingClientRect().height) })""")
        print('layout:', json.dumps(lay, ensure_ascii=False))

        await b.close()

    print('--- console errors ---')
    for e in errs: print('  ERR', e)
    print('--- page errors ---')
    for e in pageerrs: print('  PAGEERR', e)
    print('--- warnings (max 5) ---')
    for w in warns[:5]: print('  WARN', w)
    print('RESULT', 'FAIL' if (pageerrs or errs) else 'OK')


asyncio.run(main())
