<script>
/* =========================================================
   🌸 벚꽃 흩날림 + 🎵 벚꽃 노래
   - 그림: Canvas 로 직접 그린 꽃잎/꽃송이 (외부 이미지 없음)
   - 소리: 오르골 멜로디를 스크립트에서 16-bit PCM WAV 로 합성해
           <audio loop playsinline> 로 재생 (모바일 웹뷰에서 가장 확실)
           → <audio> 가 막히는 환경이면 Web Audio 로 자동 전환
   ========================================================= */
(function () {
  'use strict';
  var LS_SAKURA = 'jp_sakura_on';
  var LS_MUSIC = 'jp_music_on';
  var reduce = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  function rand(a, b) { return a + Math.random() * (b - a); }

  /* ---------------- 🌸 벚꽃 캔버스 ---------------- */
  var cv = document.getElementById('sakura');
  var ctx = cv && cv.getContext ? cv.getContext('2d') : null;
  var petals = [], W = 0, H = 0, dpr = 1, rafId = null, lastT = 0, sakuraOn = true;
  var PINK = ['#ff5c93', '#ff7aa8', '#ff9ebc'];
  var EDGE = ['#d92f6c', '#e04d85', '#e96f9c'];

  function makePetal(init) {
    var blossom = Math.random() < 0.26;                 /* 꽃송이(5장) 26% 섞기 */
    var r = blossom ? rand(6.8, 10.2) : rand(6, 12.5);  /* 기존 3.4~8 → 약 1.5~1.8배 */
    var k = Math.floor(Math.random() * 3);
    return {
      x: Math.random() * (W || 390),
      y: init ? Math.random() * (H || 844) : -30 - Math.random() * 90,
      r: r,
      blossom: blossom,
      rot: Math.random() * Math.PI * 2,
      rotV: rand(-0.6, 0.6),
      vy: rand(15, 32),
      vx: rand(-12, 12),
      sway: rand(16, 42),
      ph: Math.random() * Math.PI * 2,
      phV: rand(0.4, 0.95),
      a: rand(0.76, 0.95),                            /* 투명도 0.75~0.95 */
      col: PINK[k],
      edge: EDGE[k]
    };
  }
  function buildPetals() {
    var n = reduce ? 12 : Math.round((W * H) / 3700);
    n = Math.max(64, Math.min(96, n));                /* 최소 64장 ~ 최대 96장 */
    petals = [];
    for (var i = 0; i < n; i++) petals.push(makePetal(true));
  }
  function sizeCanvas() {
    if (!cv || !ctx) return;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = cv.clientWidth || window.innerWidth;
    H = cv.clientHeight || window.innerHeight;
    cv.width = Math.round(W * dpr);
    cv.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    buildPetals();
  }
  function drawPetal(p) {
    var r = p.r;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.globalAlpha = p.a;
    if (p.blossom) {
      /* 다섯 장이 모인 꽃송이 */
      var pr = r * 0.66;
      ctx.fillStyle = p.col;
      ctx.strokeStyle = p.edge;
      ctx.lineWidth = 1;
      for (var i = 0; i < 5; i++) {
        ctx.save();
        ctx.rotate(i * Math.PI * 2 / 5);
        ctx.beginPath();
        ctx.moveTo(0, -r * 0.14);
        ctx.bezierCurveTo(pr * 1.02, -r * 0.58, pr * 0.6, -r * 0.98, 0, -r * 0.92);
        ctx.bezierCurveTo(-pr * 0.6, -r * 0.98, -pr * 1.02, -r * 0.58, 0, -r * 0.14);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        ctx.restore();
      }
      ctx.globalAlpha = p.a * 0.95;
      ctx.fillStyle = '#ffe98a';
      ctx.beginPath();
      ctx.arc(0, 0, Math.max(1.3, r * 0.18), 0, Math.PI * 2);
      ctx.fill();
    } else {
      /* 꽃잎 한 장 — 회전에 맞춰 좌우로 살짝 접혀 날리는 느낌 */
      var fx = 0.62 + 0.38 * Math.abs(Math.cos(p.ph));
      ctx.scale(fx, 1);
      ctx.beginPath();
      ctx.moveTo(0, -r * 0.96);
      ctx.bezierCurveTo(r * 0.94, -r * 0.64, r * 0.74, r * 0.62, 0, r * 0.98);
      ctx.bezierCurveTo(-r * 0.74, r * 0.62, -r * 0.94, -r * 0.64, 0, -r * 0.96);
      ctx.closePath();
      ctx.fillStyle = p.col;
      ctx.fill();
      ctx.lineWidth = 1.1;
      ctx.strokeStyle = p.edge;
      ctx.stroke();
      ctx.globalAlpha = p.a * 0.5;
      ctx.fillStyle = '#fff3f7';
      ctx.beginPath();
      ctx.ellipse(r * 0.03, -r * 0.3, r * 0.28, r * 0.34, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }
  function frame(t) {
    rafId = null;
    if (!sakuraOn || !ctx) return;
    var dt = lastT ? Math.min((t - lastT) / 1000, 0.05) : 0.016;
    lastT = t;
    ctx.clearRect(0, 0, W, H);
    for (var i = 0; i < petals.length; i++) {
      var p = petals[i];
      p.ph += p.phV * dt;
      p.y += p.vy * dt;
      p.x += (p.vx + Math.sin(p.ph) * p.sway) * dt;
      p.rot += p.rotV * dt;
      if (p.y - p.r > H + 20) { petals[i] = makePetal(false); continue; }
      if (p.x < -40) p.x = W + 30;
      else if (p.x > W + 40) p.x = -30;
      drawPetal(p);
    }
    rafId = requestAnimationFrame(frame);
  }
  function startSakura() {
    if (!ctx) return;
    sakuraOn = true;
    cv.hidden = false;
    if (reduce) { ctx.clearRect(0, 0, W, H); petals.forEach(drawPetal); return; }
    lastT = 0;
    if (!rafId) rafId = requestAnimationFrame(frame);
  }
  function stopSakura() {
    sakuraOn = false;
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    if (ctx) ctx.clearRect(0, 0, W, H);
  }

  /* ---------------- 🎵 벚꽃 노래 (WAV 합성) ---------------- */
  var SR = 22050;          /* 샘플레이트 */
  var LOOP = 16;           /* 16초 루프 */
  var BEAT = 0.5;          /* 120 BPM */
  var BASE = 293.66;       /* D4 */
  /* 일본풍 5음계(D E G A B) 멜로디 — [반음, 박] 8마디 = 32박 = 16초 */
  var MEL = [
    [14, 1], [12, 1], [9, 1], [7, 1],
    [5, 1], [7, 1], [9, 2],
    [12, 1], [14, 1], [12, 1], [9, 1],
    [7, 2], [5, 1], [2, 1],
    [5, 1], [7, 1], [9, 1], [12, 1],
    [14, 1.5], [12, 0.5], [9, 1], [7, 1],
    [9, 1], [7, 1], [5, 2],
    [2, 1], [5, 1], [0, 2]
  ];
  var ROOTS = [0, 5, 9, 7, 5, 9, 5, 0];   /* 마디별 베이스(한 옥타브 아래) */

  function freqOf(semi) { return BASE * Math.pow(2, semi / 12); }

  /* 오르골 한 음: 4개 배음 + 지수 감쇠, 루프 끝 여운은 앞머리로 감아 끊김 없음 */
  function addBell(buf, startSec, freq, dur, gain) {
    var n = buf.length;
    var total = Math.floor((dur + 1.9) * SR);
    var idx = Math.floor(startSec * SR) % n;
    var parts = [[1, 1.0, Math.max(0.34, dur * 0.5)], [2.002, 0.34, 0.62], [3.008, 0.13, 0.34], [4.21, 0.06, 0.2]];
    var atk = 14;
    for (var p = 0; p < parts.length; p++) {
      var mul = parts[p][0], amp = parts[p][1] * gain, tau = parts[p][2];
      var w = 2 * Math.PI * freq * mul / SR;
      var c2 = 2 * Math.cos(w);
      var ym1 = -Math.sin(w), y0 = 0, env = amp;
      var dec = Math.exp(-1 / (tau * SR));
      var j = idx;
      for (var i = 0; i < total; i++) {
        var y = c2 * y0 - ym1;
        ym1 = y0; y0 = y;
        var s = y * env;
        if (i < atk) s *= i / atk;
        buf[j] += s;
        env *= dec;
        if (++j === n) j = 0;
      }
    }
  }
  function addBass(buf, startSec, freq, gain) {
    var n = buf.length;
    var total = Math.floor(2.6 * SR);
    var j = Math.floor(startSec * SR) % n;
    var w = 2 * Math.PI * freq / SR, w2 = w * 2;
    var c2a = 2 * Math.cos(w), c2b = 2 * Math.cos(w2);
    var ya1 = -Math.sin(w), ya0 = 0, yb1 = -Math.sin(w2), yb0 = 0;
    var env = gain, dec = Math.exp(-1 / (1.1 * SR));
    for (var i = 0; i < total; i++) {
      var ya = c2a * ya0 - ya1; ya1 = ya0; ya0 = ya;
      var yb = c2b * yb0 - yb1; yb1 = yb0; yb0 = yb;
      var s = (ya + 0.22 * yb) * env;
      if (i < 16) s *= i / 16;
      buf[j] += s;
      env *= dec;
      if (++j === n) j = 0;
    }
  }
  function composeLoop() {
    var n = Math.round(SR * LOOP);
    var buf = new Float32Array(n);
    var t = 0;
    for (var i = 0; i < MEL.length; i++) {
      var f = freqOf(MEL[i][0]), beats = MEL[i][1];
      addBell(buf, t, f, beats * BEAT, 0.30);
      if (i % 2 === 0) addBell(buf, t, f * 2, beats * BEAT * 0.5, 0.055);  /* 옥타브 위 반짝임 */
      t += beats * BEAT;
    }
    var bar = BEAT * 4;
    for (var b = 0; b < ROOTS.length; b++) {
      addBass(buf, b * bar, freqOf(ROOTS[b] - 24), 0.17);
    }
    for (var c = 0; c < ROOTS.length; c += 2) {
      var cf = freqOf(ROOTS[c] - 12);
      addBell(buf, c * bar, cf, 2.2, 0.05);
      addBell(buf, c * bar, cf * 1.5, 2.2, 0.045);
    }
    var peak = 0, k, a;
    for (k = 0; k < n; k++) { a = buf[k] < 0 ? -buf[k] : buf[k]; if (a > peak) peak = a; }
    var g = peak > 0 ? 0.9 / peak : 1;
    for (k = 0; k < n; k++) buf[k] *= g;
    return buf;
  }
  function statsOf(buf) {
    var peak = 0, sum = 0, n = buf.length;
    for (var i = 0; i < n; i++) {
      var a = buf[i] < 0 ? -buf[i] : buf[i];
      if (a > peak) peak = a;
      sum += buf[i] * buf[i];
    }
    return { seconds: n / SR, sampleRate: SR, peak: +peak.toFixed(4), rms: +Math.sqrt(sum / n).toFixed(4), samples: n };
  }
  function encodeWav(f32, sampleRate) {
    var n = f32.length;
    var buffer = new ArrayBuffer(44 + n * 2);
    var v = new DataView(buffer);
    function ws(off, s) { for (var i = 0; i < s.length; i++) v.setUint8(off + i, s.charCodeAt(i)); }
    ws(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); ws(8, 'WAVE');
    ws(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, sampleRate, true); v.setUint32(28, sampleRate * 2, true);
    v.setUint16(32, 2, true); v.setUint16(34, 16, true);
    ws(36, 'data'); v.setUint32(40, n * 2, true);
    for (var i = 0; i < n; i++) {
      var s = f32[i];
      s = s < -1 ? -1 : (s > 1 ? 1 : s);
      v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return new Blob([buffer], { type: 'audio/wav' });
  }

  /* ---------------- <audio> 재생기 ---------------- */
  var audioEl = null, wavUrl = null, wavReady = false, musicOn = false, fallbackOn = false;

  function ensureAudio() {
    if (audioEl) return audioEl;
    audioEl = document.createElement('audio');
    audioEl.id = 'bgm';
    audioEl.loop = true;
    audioEl.preload = 'auto';
    audioEl.setAttribute('playsinline', '');
    audioEl.setAttribute('webkit-playsinline', '');
    audioEl.setAttribute('aria-hidden', 'true');
    audioEl.style.display = 'none';
    audioEl.volume = 0.8;
    document.body.appendChild(audioEl);
    return audioEl;
  }
  function buildWav() {
    if (wavReady) return true;
    try {
      var buf = composeLoop();
      var blob = encodeWav(buf, SR);
      wavUrl = URL.createObjectURL(blob);
      ensureAudio().src = wavUrl;
      wavReady = true;
      window.__bgmStats = statsOf(buf);
      window.__bgmUrl = wavUrl;
      return true;
    } catch (e) {
      if (window.console) console.warn('BGM 합성 실패', e);
      return false;
    }
  }

  /* ---- Web Audio 대체 엔진 (<audio> 가 막힌 웹뷰용) ---- */
  var actx = null, master = null, timer = null, nextT = 0, step = 0;
  var SCALE = [293.66, 329.63, 392.0, 440.0, 493.88, 587.33, 659.25];
  var BASS = [146.83, 164.81, 196.0, 130.81];
  function makeImpulse(sec) {
    var len = Math.floor(actx.sampleRate * sec);
    var b = actx.createBuffer(2, len, actx.sampleRate);
    for (var c = 0; c < 2; c++) {
      var d = b.getChannelData(c);
      for (var i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2.6);
    }
    return b;
  }
  function initAudio() {
    if (actx) return true;
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return false;
    try { actx = new AC(); } catch (e) { return false; }
    master = actx.createGain();
    master.gain.value = 0.0001;
    var dry = actx.createGain(); dry.gain.value = 0.9;
    var conv = actx.createConvolver(); conv.buffer = makeImpulse(1.6);
    var wet = actx.createGain(); wet.gain.value = 0.26;
    master.connect(dry); dry.connect(actx.destination);
    master.connect(conv); conv.connect(wet); wet.connect(actx.destination);
    return true;
  }
  function bell(freq, at, dur, gain, type) {
    var o1 = actx.createOscillator(), o2 = actx.createOscillator();
    var g = actx.createGain(), g2 = actx.createGain();
    o1.type = type || 'sine'; o1.frequency.value = freq;
    o2.type = 'sine'; o2.frequency.value = freq * 2.004; g2.gain.value = 0.16;
    o1.connect(g); o2.connect(g2); g2.connect(g);
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(Math.max(gain, 0.001), at + 0.035);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    g.connect(master);
    o1.start(at); o1.stop(at + dur + 0.06);
    o2.start(at); o2.stop(at + dur + 0.06);
  }
  function schedule() {
    if (!fallbackOn || !actx) return;
    var now = actx.currentTime;
    if (nextT < now + 0.05) nextT = now + 0.12;
    while (nextT < now + 0.9) {
      var item = MEL[step % MEL.length];
      var dur = item[1] * BEAT;
      var idx = Math.round(item[0] / 2);
      bell(SCALE[Math.max(0, Math.min(SCALE.length - 1, idx))], nextT, Math.min(dur * 1.9, 2.4), 0.28);
      if (step % 4 === 0) bell(freqOf(MEL[step % MEL.length][0] - 12), nextT, 2.1, 0.1);
      if (step % 8 === 0) bell(BASS[Math.floor(step / 8) % BASS.length], nextT, 3.2, 0.2, 'triangle');
      nextT += dur;
      step++;
    }
  }
  function startFallback() {
    if (!initAudio()) return;
    if (actx.state === 'suspended' && actx.resume) actx.resume();
    fallbackOn = true;
    nextT = actx.currentTime + 0.2;
    step = 0;
    var t = actx.currentTime;
    master.gain.cancelScheduledValues(t);
    master.gain.setValueAtTime(Math.max(master.gain.value, 0.0001), t);
    master.gain.exponentialRampToValueAtTime(0.8, t + 1.2);   /* 0.3 → 0.8 */
    if (timer) clearInterval(timer);
    timer = setInterval(schedule, 220);
    schedule();
  }
  function stopFallback() {
    fallbackOn = false;
    if (timer) { clearInterval(timer); timer = null; }
    if (actx && master) {
      var t = actx.currentTime;
      master.gain.cancelScheduledValues(t);
      master.gain.setValueAtTime(Math.max(master.gain.value, 0.0001), t);
      master.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);
    }
  }
  function unlockCtx() {
    if (!initAudio()) return;
    if (actx.state === 'suspended' && actx.resume) actx.resume();
  }

  /* ---------------- 재생 / 정지 ---------------- */
  function startMusic() {
    musicOn = true;
    var built = buildWav();
    var el = ensureAudio();
    if (built) {
      el.volume = 0.8;
      try { el.currentTime = 0; } catch (e) {}
      var p = el.play();
      if (p && p.then) {
        p.then(function () {
          /* 실제로 소리가 흐르는지 0.6초 뒤 확인, 아니면 Web Audio 로 전환 */
          setTimeout(function () {
            if (musicOn && (el.paused || el.currentTime < 0.05)) {
              try { el.pause(); } catch (e) {}
              startFallback();
            }
          }, 650);
        }).catch(function () { startFallback(); });
      } else {
        setTimeout(function () {
          if (musicOn && (el.paused || el.currentTime < 0.05)) startFallback();
        }, 650);
      }
    } else {
      startFallback();
    }
    try { unlockCtx(); } catch (e) {}
    paintMusic();
  }
  function stopMusic() {
    musicOn = false;
    if (audioEl && !audioEl.paused) { try { audioEl.pause(); } catch (e) {} }
    stopFallback();
    paintMusic();
  }

  /* ---------------- 버튼 / UI ---------------- */
  var btnSakura = document.getElementById('btnSakura');
  var btnMusic = document.getElementById('btnMusic');
  var toastEl = document.getElementById('toast');
  var toastTimer = null;
  function toastSafe(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 2600);
  }
  function paintSakura() {
    if (!btnSakura) return;
    btnSakura.setAttribute('aria-pressed', String(sakuraOn));
    btnSakura.setAttribute('aria-label', sakuraOn ? '벚꽃 효과 끄기' : '벚꽃 효과 켜기');
    btnSakura.classList.toggle('off', !sakuraOn);
  }
  var hintDone = false;
  function paintMusic() {
    if (!btnMusic) return;
    btnMusic.setAttribute('aria-pressed', String(musicOn));
    btnMusic.classList.toggle('off', !musicOn);
    btnMusic.classList.toggle('hint', !musicOn && !hintDone);
    btnMusic.setAttribute('aria-label', musicOn ? '벚꽃 노래 끄기' : '벚꽃 노래 켜기');
    btnMusic.title = musicOn ? '벚꽃 노래 끄기' : '벚꽃 노래 켜기';
    var txt = btnMusic.querySelector('.mc-txt');
    if (txt) txt.textContent = musicOn ? '노래 끄기' : '노래 켜기';
    var ico = btnMusic.querySelector('.mc-ico');
    if (ico) ico.textContent = musicOn ? '🎶' : '🎵';
  }
  function setSakura(on) {
    if (on) startSakura(); else stopSakura();
    paintSakura();
    try { localStorage.setItem(LS_SAKURA, on ? '1' : '0'); } catch (e) {}
  }
  function setMusic(on, quiet) {
    hintDone = true;
    if (on) {
      startMusic();
      try { localStorage.setItem(LS_MUSIC, '1'); } catch (e) {}
      if (!quiet) toastSafe('🎶 벚꽃 노래를 켰어요 · 위 버튼으로 끌 수 있어요');
    } else {
      stopMusic();
      try { localStorage.setItem(LS_MUSIC, '0'); } catch (e) {}
      if (!quiet) toastSafe('🔇 노래를 껐어요');
    }
    paintMusic();
  }
  if (btnSakura) btnSakura.addEventListener('click', function () { setSakura(!sakuraOn); });
  if (btnMusic) {
    btnMusic.addEventListener('click', function (e) {
      e.preventDefault();
      setMusic(!musicOn);
    });
  }

  /* ---------------- 시작 상태 ---------------- */
  var wantSakura = true;
  try { wantSakura = localStorage.getItem(LS_SAKURA) !== '0'; } catch (e) {}
  sizeCanvas();
  paintSakura();
  paintMusic();
  setTimeout(function () { hintDone = true; paintMusic(); }, 12000);
  if (wantSakura) startSakura(); else { sakuraOn = false; cv.hidden = true; paintSakura(); }

  /* WAV 는 화면이 뜬 뒤 한가할 때 미리 만들어 둔다 (첫 터치에 바로 소리) */
  function warm() { if (!wavReady) buildWav(); }
  if (window.requestIdleCallback) setTimeout(function () { requestIdleCallback(warm, { timeout: 2500 }); }, 900);
  else setTimeout(warm, 1400);

  /* 한 번 끄기 전에는, 화면 아무 곳이나 처음 터치하면 노래가 시작된다 */
  var wantMusic = true;
  try { wantMusic = localStorage.getItem(LS_MUSIC) !== '0'; } catch (e) {}
  if (wantMusic) {
    var kick = function (ev) {
      if (btnMusic && ev && ev.target && btnMusic.contains(ev.target)) return;  /* 칩 자체 클릭은 칩이 처리 */
      document.removeEventListener('pointerdown', kick, true);
      document.removeEventListener('touchstart', kick, true);
      if (!musicOn) setMusic(true, true);
    };
    document.addEventListener('pointerdown', kick, true);
    document.addEventListener('touchstart', kick, true);
  }

  var rzT = null;
  window.addEventListener('resize', function () {
    clearTimeout(rzT);
    rzT = setTimeout(function () {
      sizeCanvas();
      if (sakuraOn) { if (rafId) { cancelAnimationFrame(rafId); rafId = null; } startSakura(); }
    }, 180);
  });
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
      if (audioEl && !audioEl.paused) { try { audioEl.pause(); } catch (e) {} }
    } else {
      if (sakuraOn && !reduce) { lastT = 0; if (!rafId) rafId = requestAnimationFrame(frame); }
      if (musicOn && audioEl && audioEl.paused && !fallbackOn) {
        var p = audioEl.play();
        if (p && p.catch) p.catch(function () {});
      }
    }
  });
})();
</script>
</body>
</html>
