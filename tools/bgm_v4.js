  /* ---------------- 🎵 노래 3곡 (WAV 합성) ----------------
     ① 🌸 사쿠라 사쿠라      — 일본 민요(전통곡·작곡자 미상, 퍼블릭 도메인) · 미야코부시 5음계 · 4/4
     ② 🌙 달빛 오르골 왈츠   — 자체 작곡 · 3/4 왈츠(저작권 문제 없음)
     ③ 🎹 설레는 여행 오르골 — 자체 작곡 · 요(陽) 5음계 · 4/4
     모두 이 자리에서 16-bit PCM WAV 로 합성하고 <audio loop> 로 재생합니다.
     (음원 파일을 따로 받아 오지 않아 저작권·통신 문제가 없습니다)
     ========================================================= */
  var SR = 22050;                                    /* 샘플레이트 */
  var SEMI = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  function freqOf(name) {
    var m = /^([A-G])([#b]?)(-?\d)$/.exec(name || '');
    if (!m) return 440;
    var midi = (parseInt(m[3], 10) + 1) * 12 + SEMI[m[1]] + (m[2] === '#' ? 1 : m[2] === 'b' ? -1 : 0);
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  var TRACKS = [
    /* ① 사쿠라 사쿠라 — 14마디 × 4박, 한 박 0.35초 → 약 19.6초 */
    {
      id: 'sakura', emoji: '🌸', name: '사쿠라 사쿠라', short: '사쿠라',
      note: '일본 벚꽃 민요 · 4/4',
      beat: 0.35, meter: 4, accomp: 'pad',
      mel: [
        ['A4', 1], ['A4', 1], ['B4', 2],
        ['A4', 1], ['A4', 1], ['B4', 2],
        ['A4', 1], ['B4', 1], ['C5', 1], ['B4', 1],
        ['A4', 1], ['B4', 0.5], ['A4', 0.5], ['F4', 2],
        ['E4', 1], ['C4', 1], ['E4', 1], ['F4', 1],
        ['E4', 1], ['E4', 0.5], ['C4', 0.5], ['B3', 2],
        ['A4', 1], ['B4', 1], ['C5', 1], ['B4', 1],
        ['A4', 1], ['B4', 0.5], ['A4', 0.5], ['F4', 2],
        ['E4', 1], ['C4', 1], ['E4', 1], ['F4', 1],
        ['E4', 1], ['E4', 0.5], ['C4', 0.5], ['B3', 2],
        ['A4', 1], ['A4', 1], ['B4', 2],
        ['A4', 1], ['A4', 1], ['B4', 2],
        ['E4', 1], ['F4', 1], ['B4', 0.5], ['A4', 0.5], ['F4', 1],
        ['E4', 4]
      ],
      chords: {
        A: { bass: 'A2', notes: ['E3', 'A3', 'C4'] },
        F: { bass: 'F2', notes: ['C3', 'F3', 'A3'] },
        E: { bass: 'E2', notes: ['B2', 'E3', 'B3'] }
      },
      bars: ['A', 'A', 'A', 'F', 'A', 'E', 'A', 'F', 'A', 'E', 'A', 'A', 'F', 'E']
    },
    /* ② 달빛 오르골 왈츠 — 자체 작곡. 16마디 × 3박, 한 박 0.42초 → 약 20.2초 */
    {
      id: 'moon', emoji: '🌙', name: '달빛 오르골 왈츠', short: '달빛 왈츠',
      note: '직접 만든 3/4 왈츠',
      beat: 0.42, meter: 3, accomp: 'waltz',
      mel: [
        ['C5', 1], ['A4', 1], ['F4', 1],
        ['A4', 2], ['C5', 1],
        ['D5', 1], ['C5', 1], ['A4', 1],
        ['G4', 3],
        ['C5', 1], ['A4', 1], ['F4', 1],
        ['A4', 2], ['Bb4', 1],
        ['C5', 1], ['D5', 1], ['E5', 1],
        ['F5', 3],
        ['E5', 1], ['D5', 1], ['C5', 1],
        ['D5', 2], ['Bb4', 1],
        ['C5', 1], ['A4', 1], ['F4', 1],
        ['G4', 3],
        ['A4', 1], ['C5', 1], ['F5', 1],
        ['E5', 2], ['D5', 1],
        ['C5', 2], ['A4', 1],
        ['F4', 3]
      ],
      chords: {
        F: { bass: 'F2', notes: ['F3', 'A3', 'C4'] },
        Bb: { bass: 'Bb2', notes: ['D4', 'F4'] },
        C: { bass: 'C3', notes: ['G3', 'C4', 'E4'] }
      },
      bars: ['F', 'F', 'Bb', 'C', 'F', 'Bb', 'C', 'F', 'C', 'Bb', 'F', 'C', 'F', 'C', 'F', 'F']
    },
    /* ③ 설레는 여행 오르골 — 자체 작곡. 16마디 × 4박, 한 박 0.30초 → 약 19.2초 */
    {
      id: 'trip', emoji: '🎹', name: '설레는 여행 오르골', short: '여행 오르골',
      note: '직접 만든 5음계 여행 멜로디',
      beat: 0.30, meter: 4, accomp: 'pad',
      mel: [
        ['D5', 1], ['E5', 1], ['G5', 1], ['E5', 1],
        ['D5', 2], ['B4', 2],
        ['G4', 1], ['A4', 1], ['B4', 1], ['D5', 1],
        ['D5', 4],
        ['B4', 1], ['D5', 1], ['E5', 1], ['D5', 1],
        ['A4', 2], ['B4', 2],
        ['D5', 1], ['B4', 1], ['A4', 1], ['G4', 1],
        ['G4', 4],
        ['E5', 1], ['G5', 1], ['E5', 1], ['D5', 1],
        ['B4', 2], ['D5', 2],
        ['E5', 1], ['D5', 1], ['B4', 1], ['A4', 1],
        ['D5', 4],
        ['G5', 1], ['E5', 1], ['D5', 1], ['B4', 1],
        ['A4', 2], ['B4', 2],
        ['D5', 1], ['E5', 1], ['G5', 2],
        ['E5', 1], ['D5', 3]
      ],
      chords: {
        D: { bass: 'D2', notes: ['A3', 'D4'] },
        G: { bass: 'G2', notes: ['B3', 'D4'] },
        A: { bass: 'A2', notes: ['A3', 'E4'] }
      },
      bars: ['D', 'G', 'D', 'D', 'D', 'A', 'G', 'G', 'G', 'D', 'A', 'D', 'G', 'A', 'D', 'D']
    }
  ];

  function trackOf(i) { return TRACKS[((i % TRACKS.length) + TRACKS.length) % TRACKS.length]; }
  function indexOfTrack(id) { for (var i = 0; i < TRACKS.length; i++) if (TRACKS[i].id === id) return i; return -1; }
  function melBeats(t) { var s = 0; for (var i = 0; i < t.mel.length; i++) s += t.mel[i][1]; return s; }
  function loopLen(t) { return melBeats(t) * t.beat; }
  /* 각 음이 몇 번째 마디에 속하는지 (Web Audio 대체 엔진용) */
  TRACKS.forEach(function (t) {
    var out = [], beat = 0;
    for (var i = 0; i < t.mel.length; i++) { out.push(Math.floor(beat / t.meter + 1e-9)); beat += t.mel[i][1]; }
    t.melbar = out;
  });

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
  /* 따뜻한 저음 화음 패드: 천천히 부풀었다 잦아드는 사인 패드 */
  function addPad(buf, startSec, freqs, dur, gain) {
    var n = buf.length;
    var total = Math.floor((dur + 0.55) * SR);
    var j0 = Math.floor(startSec * SR) % n;
    var atk = Math.floor(0.24 * SR);
    var rel = Math.floor(0.45 * SR);
    var sus = total - atk - rel; if (sus < 0) sus = 0;
    for (var f = 0; f < freqs.length; f++) {
      var freq = freqs[f], g = gain / Math.sqrt(freqs.length);
      var w = 2 * Math.PI * freq / SR, w2 = w * 2;
      var c2 = 2 * Math.cos(w), ym1 = -Math.sin(w), y0 = 0;
      var c2b = 2 * Math.cos(w2), yb1 = -Math.sin(w2), yb0 = 0;
      var j = j0;
      for (var i = 0; i < total; i++) {
        var y = c2 * y0 - ym1; ym1 = y0; y0 = y;
        var yb = c2b * yb0 - yb1; yb1 = yb0; yb0 = yb;
        var env;
        if (i < atk) env = i / atk;
        else if (i < atk + sus) env = 1;
        else env = 1 - (i - atk - sus) / rel;
        if (env < 0) env = 0;
        buf[j] += (y + 0.16 * yb) * env * g;
        if (++j === n) j = 0;
      }
    }
  }
  function addBass(buf, startSec, freq, gain) {
    var n = buf.length;
    var total = Math.floor(2.6 * SR);
    var j = Math.floor(startSec * SR) % n;
    var w = 2 * Math.PI * freq / SR, w2 = w * 2;
    var c2a = 2 * Math.cos(w), c2b = Math.cos(w2) * 2;
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

  function composeTrack(t) {
    var n = Math.round(SR * loopLen(t));
    var buf = new Float32Array(n);
    var time = 0, i, k;
    /* 멜로디 */
    for (i = 0; i < t.mel.length; i++) {
      var nm = t.mel[i][0], beats = t.mel[i][1], dur = beats * t.beat;
      if (nm !== '-') {
        var f = freqOf(nm);
        addBell(buf, time, f, dur, 0.30);
        if (i % 2 === 0) addBell(buf, time, f * 2, dur * 0.5, 0.05);   /* 옥타브 위 반짝임 */
      }
      time += dur;
    }
    /* 반주 — 마디마다 */
    var barLen = t.meter * t.beat;
    for (var b = 0; b < t.bars.length; b++) {
      var ch = t.chords[t.bars[b]];
      if (!ch) continue;
      var s = b * barLen;
      if (t.accomp === 'waltz') {
        /* 왈츠: 1박에 낮은 베이스, 2·3박에 가볍게 화음 퉁기기 */
        addBass(buf, s, freqOf(ch.bass), 0.05);
        for (k = 1; k < t.meter; k++) {
          for (var q = 0; q < ch.notes.length; q++) {
            addBell(buf, s + k * t.beat, freqOf(ch.notes[q]), t.beat * 0.55, 0.034);
          }
        }
      } else {
        var fs = [];
        for (var q2 = 0; q2 < ch.notes.length; q2++) fs.push(freqOf(ch.notes[q2]));
        addPad(buf, s, fs, barLen, 0.092);
        addBass(buf, s, freqOf(ch.bass), 0.052);
      }
    }
    /* 정규화 */
    var peak = 0, a;
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
    return { seconds: +(n / SR).toFixed(2), sampleRate: SR, peak: +peak.toFixed(3), rms: +Math.sqrt(sum / n).toFixed(4), samples: n };
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

  /* ---------------- <audio> 재생기 (곡마다 WAV 를 만들어 캐시) ---------------- */
  var audioEl = null, musicOn = false, fallbackOn = false, trackIndex = 0;
  var wavCache = {}, buildMs = {};

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
  function prepare(i) {
    var t = trackOf(i);
    if (wavCache[t.id]) return wavCache[t.id];
    var t0 = (window.performance && performance.now) ? performance.now() : 0;
    try {
      var buf = composeTrack(t);
      var blob = encodeWav(buf, SR);
      var rec = { url: URL.createObjectURL(blob), stats: statsOf(buf), seconds: loopLen(t) };
      wavCache[t.id] = rec;
      buildMs[t.id] = t0 ? Math.round(window.performance.now() - t0) : null;
      window.__bgmStats = rec.stats;            /* 이전 검증 스크립트와 호환 */
      return rec;
    } catch (e) {
      if (window.console) console.warn('BGM 합성 실패', t.id, e);
      return null;
    }
  }

  /* ---- Web Audio 대체 엔진 (<audio> 가 막힌 웹뷰용) ---- */
  var actx = null, master = null, timer = null, nextT = 0, step = 0, lastBar = -1;
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
  function padChord(freqs, at, dur, gain) {
    for (var i = 0; i < freqs.length; i++) {
      var o = actx.createOscillator(), g = actx.createGain();
      var amp = Math.max(gain / Math.sqrt(freqs.length), 0.0008);
      o.type = 'sine'; o.frequency.value = freqs[i];
      g.gain.setValueAtTime(0.0001, at);
      g.gain.exponentialRampToValueAtTime(amp, at + dur * 0.35);
      g.gain.exponentialRampToValueAtTime(0.0001, at + dur * 1.3);
      o.connect(g); g.connect(master);
      o.start(at); o.stop(at + dur * 1.4 + 0.05);
    }
  }
  function schedule() {
    if (!fallbackOn || !actx) return;
    var t = trackOf(trackIndex);
    var now = actx.currentTime;
    if (nextT < now + 0.05) nextT = now + 0.12;
    while (nextT < now + 0.9) {
      var k = step % t.mel.length;
      var item = t.mel[k];
      var dur = item[1] * t.beat;
      if (item[0] !== '-') bell(freqOf(item[0]), nextT, Math.min(dur * 1.9, 2.2), 0.26);
      var bar = t.melbar[k];
      if (bar !== lastBar) {                       /* 마디가 바뀔 때 반주 */
        var ch = t.chords[t.bars[bar % t.bars.length]];
        if (ch) {
          var notes = [];
          for (var q = 0; q < ch.notes.length; q++) notes.push(freqOf(ch.notes[q]));
          if (t.accomp === 'waltz') {
            bell(freqOf(ch.bass), nextT, 1.5, 0.16);
            for (var j = 1; j < t.meter; j++) padChord(notes, nextT + j * t.beat, t.beat * 0.85, 0.07);
          } else {
            bell(freqOf(ch.bass), nextT, 1.7, 0.14);
            padChord(notes, nextT, t.meter * t.beat, 0.13);
          }
        }
        lastBar = bar;
      }
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
    lastBar = -1;
    var t = actx.currentTime;
    master.gain.cancelScheduledValues(t);
    master.gain.setValueAtTime(Math.max(master.gain.value, 0.0001), t);
    master.gain.exponentialRampToValueAtTime(0.8, t + 1.2);
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

  /* ---------------- 재생 / 정지 / 곡 바꾸기 ---------------- */
  function pauseAll() {
    if (audioEl && !audioEl.paused) { try { audioEl.pause(); } catch (e) {} }
    stopFallback();
  }
  function playCurrent(quiet) {
    musicOn = true;
    var t = trackOf(trackIndex);
    var rec = prepare(trackIndex);
    var el = ensureAudio();
    if (rec) {
      if (el.getAttribute('src') !== rec.url) el.src = rec.url;
      el.volume = 0.8;
      try { el.currentTime = 0; } catch (e) {}
      var p = el.play();
      if (p && p.then) {
        p.then(function () {
          /* 실제로 소리가 흐르는지 0.6초 뒤 확인, 아니면 Web Audio 로 전환 */
          setTimeout(function () {
            if (musicOn && !fallbackOn && (el.paused || el.currentTime < 0.05)) {
              try { el.pause(); } catch (e) {}
              startFallback();
            }
          }, 650);
        }).catch(function () { if (musicOn) startFallback(); });
      } else {
        setTimeout(function () {
          if (musicOn && !fallbackOn && el.paused) startFallback();
        }, 650);
      }
      window.__bgmUrl = rec.url;
    } else {
      startFallback();
      window.__bgmUrl = null;
    }
    try { unlockCtx(); } catch (e) {}
    paintMusic();
    if (!quiet) toastSafe('🎶 ' + t.emoji + ' ' + t.name + ' — 위 버튼으로 끌 수 있어요');
  }
  function stopMusic() {
    musicOn = false;
    pauseAll();
    paintMusic();
  }
  function pickTrack(i) {
    i = ((i % TRACKS.length) + TRACKS.length) % TRACKS.length;
    var was = trackOf(trackIndex), t = trackOf(i);
    var playing = musicOn;
    trackIndex = i;
    try { localStorage.setItem(LS_TRACK, t.id); } catch (e) {}
    paintTracks();
    if (playing && t.id === was.id) { paintMusic(); return; }   /* 같은 곡을 다시 눌렀을 때는 그대로 */
    if (playing) pauseAll();
    playCurrent(true);
    toastSafe(playing
      ? '🎶 ' + t.emoji + ' ' + t.name + ' 로 바꿨어요'
      : '🎶 ' + t.emoji + ' ' + t.name + ' — 이 곡으로 켰어요');
  }

  /* ---------------- 버튼 / UI ---------------- */
  var btnSakura = document.getElementById('btnSakura');
  var btnMusic = document.getElementById('btnMusic');
  var trackChips = [].slice.call(document.querySelectorAll('.track-chip'));
  var toastEl = document.getElementById('toast');
  var toastTimer = null;
  function toastSafe(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 2800);
  }
  function paintSakura() {
    if (!btnSakura) return;
    btnSakura.setAttribute('aria-pressed', String(sakuraOn));
    btnSakura.setAttribute('aria-label', sakuraOn ? '벚꽃 흩날림 끄기 (지금 켜짐)' : '벚꽃 흩날림 켜기 (지금 꺼짐)');
    btnSakura.title = sakuraOn ? '벚꽃 흩날림 끄기' : '벚꽃 흩날림 켜기';
    btnSakura.classList.toggle('off', !sakuraOn);
    var txt = document.getElementById('sakuraTxt');
    if (txt) txt.textContent = sakuraOn ? '벚꽃 끄기' : '벚꽃 켜기';
  }
  var hintDone = false;
  function paintMusic() {
    if (!btnMusic) return;
    var t = trackOf(trackIndex);
    btnMusic.setAttribute('aria-pressed', String(musicOn));
    btnMusic.classList.toggle('off', !musicOn);
    btnMusic.classList.toggle('hint', !musicOn && !hintDone);
    btnMusic.setAttribute('aria-label', (musicOn ? '노래 끄기' : '노래 켜기') + ' (지금 ' + (musicOn ? '듣는 곡: ' + t.name : '꺼짐') + ')');
    btnMusic.title = (musicOn ? '노래 끄기' : '노래 켜기') + ' · ' + t.emoji + ' ' + t.name;
    var txt = document.getElementById('musicTxt');
    if (txt) txt.textContent = musicOn ? '노래 끄기' : '노래 켜기';
    var ico = btnMusic.querySelector('.c-ico');
    if (ico) ico.textContent = musicOn ? '🎶' : '🎵';
  }
  function paintTracks() {
    var cur = trackOf(trackIndex).id;
    for (var i = 0; i < trackChips.length; i++) {
      var chip = trackChips[i];
      var id = chip.getAttribute('data-track');
      var on = id === cur;
      chip.setAttribute('aria-pressed', String(on));
      chip.setAttribute('aria-label', (on ? '지금 듣는 곡: ' : '이 곡으로 바꾸기: ') + trackOf(indexOfTrack(id)).name);
      chip.title = trackOf(indexOfTrack(id)).note;
    }
  }
  function setSakura(on, quiet) {
    if (on) startSakura(); else stopSakura();
    paintSakura();
    try { localStorage.setItem(LS_SAKURA, on ? '1' : '0'); } catch (e) {}
    if (!quiet) toastSafe(on ? '🌸 벚꽃 흩날림을 켰어요' : '🌸 벚꽃 흩날림을 껐어요');
  }
  function setMusic(on, quiet) {
    hintDone = true;
    if (on) {
      playCurrent(quiet);
      try { localStorage.setItem(LS_MUSIC, '1'); } catch (e) {}
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
  trackChips.forEach(function (chip) {
    chip.addEventListener('click', function (e) {
      e.preventDefault();
      hintDone = true;
      var ix = indexOfTrack(chip.getAttribute('data-track'));
      if (ix >= 0) pickTrack(ix);
    });
  });

  /* ---------------- 시작 상태 ---------------- */
  var wantSakura = true;
  try { wantSakura = localStorage.getItem(LS_SAKURA) !== '0'; } catch (e) {}
  var savedTrack = null;
  try { savedTrack = localStorage.getItem(LS_TRACK); } catch (e) {}
  if (savedTrack && indexOfTrack(savedTrack) >= 0) trackIndex = indexOfTrack(savedTrack);
  sizeCanvas();
  paintSakura();
  paintMusic();
  paintTracks();
  setTimeout(function () { hintDone = true; paintMusic(); }, 12000);
  if (wantSakura) startSakura(); else { sakuraOn = false; cv.hidden = true; paintSakura(); }

  /* WAV 는 화면이 뜬 뒤 한가할 때 미리 만들어 둔다 (첫 터치에 바로 소리) */
  function warm(i) { prepare(i); }
  function warmAll() {
    warm(trackIndex);
    var rest = [];
    for (var i = 0; i < TRACKS.length; i++) if (i !== trackIndex) rest.push(i);
    var step2 = function () {
      if (!rest.length) return;
      warm(rest.shift());
      if (window.requestIdleCallback) requestIdleCallback(step2, { timeout: 3000 });
      else setTimeout(step2, 700);
    };
    if (window.requestIdleCallback) requestIdleCallback(step2, { timeout: 3000 });
    else setTimeout(step2, 700);
  }
  if (window.requestIdleCallback) setTimeout(function () { requestIdleCallback(warmAll, { timeout: 2500 }); }, 900);
  else setTimeout(warmAll, 1400);

  /* 한 번 끄기 전에는, 화면 아무 곳이나 처음 터치하면 노래가 시작된다 */
  var wantMusic = true;
  try { wantMusic = localStorage.getItem(LS_MUSIC) !== '0'; } catch (e) {}
  if (wantMusic) {
    var kick = function (ev) {
      /* 상단 칩(벚꽃·노래·곡 고르기)은 그 버튼이 직접 처리한다 */
      if (ev && ev.target && ev.target.closest && ev.target.closest('.topbar')) return;
      document.removeEventListener('pointerdown', kick, true);
      document.removeEventListener('touchstart', kick, true);
      if (!musicOn) { hintDone = true; playCurrent(true); }
    };
    document.addEventListener('pointerdown', kick, true);
    document.addEventListener('touchstart', kick, true);
  }

  /* 검증용 상태 노출 */
  window.__bgmState = function () {
    var t = trackOf(trackIndex);
    var rec = wavCache[t.id];
    return {
      track: { index: trackIndex, id: t.id, name: t.name, emoji: t.emoji, seconds: +loopLen(t).toFixed(2), bars: t.bars.length, meter: t.meter },
      tracks: TRACKS.map(function (x) { return { id: x.id, name: x.name, seconds: +loopLen(x).toFixed(2), built: !!wavCache[x.id] }; }),
      musicOn: musicOn, fallbackOn: fallbackOn, sakuraOn: sakuraOn,
      built: Object.keys(wavCache),
      stats: rec ? rec.stats : null,
      buildMs: buildMs[t.id] || null,
      audio: audioEl ? {
        paused: audioEl.paused,
        cur: +audioEl.currentTime.toFixed(2),
        dur: isFinite(audioEl.duration) ? +audioEl.duration.toFixed(2) : null,
        loop: audioEl.loop
      } : null
    };
  };
  window.__bgmUrls = function () {
    var out = {};
    for (var k in wavCache) if (wavCache.hasOwnProperty(k)) out[k] = wavCache[k].url;
    return out;
  };

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
