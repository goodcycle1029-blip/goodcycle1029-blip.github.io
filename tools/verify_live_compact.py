"""Verify the live GitHub Pages home page at phone and desktop widths.

Usage: python3 tools/verify_live_compact.py
Saves full-page screenshots to /workspace/downloads/index_compact_{mobile,desktop}.png.
"""
import json

from playwright.sync_api import sync_playwright

URL = 'https://goodcycle1029-blip.github.io/'


def main():
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w, h, name in [(390, 844, 'mobile'), (1280, 900, 'desktop')]:
            pg = b.new_page(viewport={'width': w, 'height': h},
                            device_scale_factor=2 if w == 390 else 1)
            pg.goto(URL, wait_until='networkidle')
            pg.wait_for_timeout(2200)
            info = pg.evaluate("""() => ({
              height: document.documentElement.scrollHeight,
              overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
              brokenImages: Array.from(document.images).filter(i => !i.complete || i.naturalWidth === 0).map(i => i.currentSrc || i.src),
              images: document.images.length,
              cards: Array.from(document.querySelectorAll('.card')).map(a => a.getAttribute('href')),
              ctas: Array.from(document.querySelectorAll('.more a, .head .cta')).map(a => a.getAttribute('href')),
              stat: (document.querySelector('[data-stat="total"]') || {}).textContent,
              title: document.title
            })""")
            print(name, json.dumps(info, ensure_ascii=False, indent=1))
            pg.screenshot(path=f'/workspace/downloads/index_compact_{name}.png', full_page=True)
            pg.close()
        b.close()


if __name__ == '__main__':
    main()
