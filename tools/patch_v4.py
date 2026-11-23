#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""japan.html v4 패치: ① 벚꽃 글자 라벨 칩 ② 노래 3곡 선택(곡 이름 칩) ③ sw 캐시 v12"""
import os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
HTML = os.path.join(ROOT, 'japan.html')
SRC_JS = os.path.join(HERE, 'bgm_v4.js')

src = open(HTML, encoding='utf-8').read()
new_js = open(SRC_JS, encoding='utf-8').read().rstrip('\n')

def rep(old, new, label):
    global src
    if old not in src:
        print('MISS:', label); sys.exit(1)
    if src.count(old) != 1:
        print('DUP(%d):' % src.count(old), label); sys.exit(1)
    src = src.replace(old, new, 1)
    print('ok:', label)

# ---------- 1) CSS ----------
old_css_start = "/* 🎵 노래 켜기 칩 (상단 고정, 눈에 띄게) */"
i = src.index(old_css_start)
end_marker = "@media(prefers-reduced-motion:reduce){.music-chip.hint{animation:none}.music-chip .mc-bars i{animation:none}}"
j = src.index(end_marker, i) + len(end_marker)

NEW_CSS = """/* ---------- 상단 기능 칩 (🌸 벚꽃 · 🎵 노래) ---------- */
.chip-row{display:flex;gap:8px}
.chip{
  display:flex;align-items:center;justify-content:center;gap:6px;flex:1 1 0;min-width:0;
  padding:8px 10px;border-radius:13px;border:1.5px solid var(--line);background:#fff;
  color:var(--ink2);font-weight:800;font-size:16px;letter-spacing:-.03em;line-height:1.15;
  box-shadow:0 2px 8px rgba(23,26,32,.05);
  transition:transform .12s ease,box-shadow .2s ease,background .2s ease,color .2s ease,border-color .2s ease
}
.chip:active{transform:scale(.985)}
.chip .c-ico{font-size:18px;line-height:1}
.chip .c-txt{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chip-sakura[aria-pressed="true"]{border-color:#f7b6cf;background:#fff2f7;color:#c02a5e;box-shadow:0 3px 10px rgba(214,47,110,.12)}
.chip-sakura.off{background:#fbfaf8;border-color:var(--line);color:#8b8f97}
.music-chip{border-color:#f7a8c4;color:#d62f6e}
.music-chip.hint{animation:chipGlow 2.3s ease-in-out infinite}
.music-chip[aria-pressed="true"]{
  background:linear-gradient(135deg,#ff4f8b,#ff7aa8);border-color:#ff4f8b;color:#fff;
  box-shadow:0 6px 18px rgba(255,79,139,.32)
}
.music-chip .mc-bars{display:none;align-items:flex-end;gap:2.5px;height:14px}
.music-chip .mc-bars i{width:3px;background:#fff;border-radius:2px;transform-origin:bottom;animation:eqBar .9s ease-in-out infinite}
.music-chip .mc-bars i:nth-child(1){height:7px}
.music-chip .mc-bars i:nth-child(2){height:13px;animation-delay:.18s}
.music-chip .mc-bars i:nth-child(3){height:9px;animation-delay:.36s}
.music-chip[aria-pressed="true"] .mc-bars{display:flex}
@keyframes eqBar{0%,100%{transform:scaleY(.45)}50%{transform:scaleY(1)}}
@keyframes chipGlow{0%,100%{box-shadow:0 2px 8px rgba(214,47,110,.10),0 0 0 0 rgba(255,79,139,.4)}60%{box-shadow:0 2px 8px rgba(214,47,110,.10),0 0 0 9px rgba(255,79,139,0)}}
/* 🎼 노래 3곡 고르기 */
.track-row{display:flex;gap:6px}
.track-chip{
  flex:1 1 0;min-width:0;display:flex;align-items:center;justify-content:center;gap:5px;
  padding:5px 6px;border-radius:11px;border:1.5px solid var(--line);background:#fff;
  color:var(--sub);font-weight:700;font-size:14.5px;letter-spacing:-.04em;line-height:1.2;
  white-space:nowrap;overflow:hidden;
  transition:background .18s ease,color .18s ease,border-color .18s ease,transform .1s ease
}
.track-chip:active{transform:scale(.97)}
.track-chip .t-ico{font-size:14px;line-height:1}
.track-chip[aria-pressed="true"]{background:var(--brand);border-color:var(--brand);color:#fff;box-shadow:0 3px 10px rgba(31,58,95,.22)}
@media(max-width:370px){.chip{font-size:15px;padding:7px 6px}.track-chip{font-size:13.5px;padding:5px 4px}}
@media(prefers-reduced-motion:reduce){.music-chip.hint{animation:none}.music-chip .mc-bars i{animation:none}}"""
src = src[:i] + NEW_CSS + src[j:]
print('ok: css block')

# ---------- 2) 상단 바 마크업 ----------
OLD_HEADER = """      <button class="icon-btn" id="btnSakura" type="button" aria-pressed="true" aria-label="벚꽃 효과 끄기" title="벚꽃 날리기 켜기/끄기">🌸</button>
      <button class="icon-btn" id="btnSplitTop" aria-label="마주보기 모드 열기" title="마주보기 모드">🤝</button>
    </div>
    <button class="music-chip hint off" id="btnMusic" type="button" aria-pressed="false" aria-label="벚꽃 노래 켜기" title="벚꽃 노래 켜기/끄기">
      <span class="mc-ico" aria-hidden="true">🎵</span><span class="mc-txt">노래 켜기</span>
      <span class="mc-bars" aria-hidden="true"><i></i><i></i><i></i></span>
    </button>"""

NEW_HEADER = """      <button class="icon-btn" id="btnSplitTop" aria-label="마주보기 모드 열기" title="마주보기 모드">🤝</button>
    </div>
    <div class="chip-row">
      <button class="chip chip-sakura" id="btnSakura" type="button" aria-pressed="true" aria-label="벚꽃 흩날림 끄기 (지금 켜짐)" title="벚꽃 흩날림 끄기">
        <span class="c-ico" aria-hidden="true">🌸</span><span class="c-txt" id="sakuraTxt">벚꽃 끄기</span>
      </button>
      <button class="chip music-chip hint off" id="btnMusic" type="button" aria-pressed="false" aria-label="노래 켜기 (지금 꺼짐)" title="노래 켜기 · 🌸 사쿠라 사쿠라">
        <span class="c-ico" aria-hidden="true">🎵</span><span class="c-txt" id="musicTxt">노래 켜기</span>
        <span class="mc-bars" aria-hidden="true"><i></i><i></i><i></i></span>
      </button>
    </div>
    <div class="track-row" role="group" aria-label="노래 3곡 중 고르기">
      <button class="track-chip" type="button" data-track="sakura" aria-pressed="true" aria-label="지금 듣는 곡: 사쿠라 사쿠라"><span class="t-ico" aria-hidden="true">🌸</span>사쿠라</button>
      <button class="track-chip" type="button" data-track="moon" aria-pressed="false" aria-label="이 곡으로 바꾸기: 달빛 오르골 왈츠"><span class="t-ico" aria-hidden="true">🌙</span>달빛 왈츠</button>
      <button class="track-chip" type="button" data-track="trip" aria-pressed="false" aria-label="이 곡으로 바꾸기: 설레는 여행 오르골"><span class="t-ico" aria-hidden="true">🎹</span>여행 오르골</button>
    </div>"""
rep(OLD_HEADER, NEW_HEADER, 'header markup')

# ---------- 3) 스크립트 주석 + LS_TRACK ----------
rep("""   🌸 벚꽃 흩날림 + 🎵 벚꽃 노래
   - 그림: Canvas 로 직접 그린 꽃잎/꽃송이 (외부 이미지 없음)
   - 소리: 오르골 멜로디를 스크립트에서 16-bit PCM WAV 로 합성해""",
    """   🌸 벚꽃 흩날림 + 🎵 노래 3곡(사쿠라·달빛 왈츠·여행 오르골)
   - 그림: Canvas 로 직접 그린 꽃잎/꽃송이 (외부 이미지 없음)
   - 소리: 오르골 멜로디 3곡을 스크립트에서 16-bit PCM WAV 로 합성해""",
    'script header comment')

rep("""  var LS_SAKURA = 'jp_sakura_on';
  var LS_MUSIC = 'jp_music_on';""",
    """  var LS_SAKURA = 'jp_sakura_on';
  var LS_MUSIC = 'jp_music_on';
  var LS_TRACK = 'jp_music_track';""",
    'LS_TRACK')

# ---------- 4) 음악 엔진 블록 교체 ----------
marker = "  /* ---------------- 🎵 벚꽃 노래 (WAV 합성) ----------------"
a = src.index(marker)
b = src.rindex("})();", a)
src = src[:a] + new_js + '\n' + src[b:]
print('ok: music engine block')

open(HTML, 'w', encoding='utf-8').write(src)
print('written', HTML, len(src), 'chars')
