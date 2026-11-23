#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""japan.html 의 <style> 블록 안 font-size(px) 를 키운다.
- 본문/표/버튼/탭 등 읽는 글씨는 최소 15px 이상으로 올린다.
- 기기 mockup(.machine*/.lang-btns/.fare-mini/.keypad)은 그림이라 제외하고 따로 조금만 키운다.
"""
import re, sys, io

PATH = sys.argv[1] if len(sys.argv) > 1 else 'japan.html'

src = io.open(PATH, encoding='utf-8').read()
start = src.index('<style>')
end = src.index('</style>')
css = src[start:end]
rest = src[end:]

TABLE = {
    9: 11, 9.5: 11.5, 10: 12.5, 10.5: 13.5, 11: 14, 11.5: 15, 12: 15.5,
    12.5: 16, 13: 17, 13.5: 17.5, 14: 18, 15: 19, 16: 20, 17: 21,
    18: 22, 19: 22.5, 20: 23, 22: 25, 23: 27, 24: 28, 26: 29, 28: 31, 30: 33,
}

def scale(n):
    if n in TABLE:
        return TABLE[n]
    v = n * 1.25
    if n >= 24:
        v = n + 4
    v = round(v * 2) / 2.0
    if n >= 15:
        v = max(v, 19)
    elif n >= 11:
        v = max(v, 15)
    else:
        v = max(v, 11)
    return v

# 줄 단위로 처리하되, mockup 셀렉터가 들어간 줄은 건너뛴다.
SKIP_MARKERS = ('.machine-top', '.machine-screen', '.scr-head', '.lang-btns', '.fare-mini', '.keypad')
lines = css.split('\n')
changed = 0
small = []
for i, line in enumerate(lines):
    if any(m in line for m in SKIP_MARKERS):
        small.append((i + 1, line.strip()))
        continue
    if 'clamp(' in line:
        small.append((i + 1, line.strip()))
        continue
    def repl(m):
        global changed
        n = float(m.group(2))
        v = scale(n)
        changed += 1
        return '%s%s%s' % (m.group(1), ('%g' % v), m.group(3))
    new = re.sub(r'(font-size:\s*)([0-9.]+)(px)', repl, line)
    lines[i] = new

new_css = '\n'.join(lines)

# 아주 작게 남은 글씨 목록 (검토용)
left = []
for ln in new_css.split('\n'):
    for m in re.finditer(r'font-size:\s*([0-9.]+)px', ln):
        if float(m.group(1)) < 15:
            left.append((m.group(1), ln.strip()[:110]))

io.open(PATH, 'w', encoding='utf-8').write(new_css + rest)
print('scaled declarations:', changed)
print('--- still under 15px ---')
seen = set()
for v, ln in left:
    if ln in seen:
        continue
    seen.add(ln)
    print(v, '|', ln)
print('--- skipped (mockup/clamp) ---')
for n, ln in small:
    print(n, '|', ln[:110])
