"""Serve work/company_site and render/measure the page.

Usage: python3 tools/preview.py [width] [height] [out.png] [--measure]
Starts a local static server on a random port, so it needs no external process.
"""
import json
import os
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = '/workspace'


def serve():
    handler = partial(SimpleHTTPRequestHandler, directory=ROOT)
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


MEASURE = """() => {
  const r = e => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  return {
    height: document.documentElement.scrollHeight,
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    brokenImages: Array.from(document.images).filter(i => !i.complete || i.naturalWidth === 0).map(i => i.currentSrc || i.src),
    sections: Array.from(document.querySelectorAll('header, main > section, footer')).map(s => [s.className || s.tagName, Math.round(s.getBoundingClientRect().height)]),
    more: getComputedStyle(document.querySelector('.more')).display + ' / ' + getComputedStyle(document.querySelector('.more')).gridTemplateColumns,
    moreBtns: Array.from(document.querySelectorAll('.more .btn')).map(r),
    phs: Array.from(document.querySelectorAll('.card .ph')).map(r)
  };
}"""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    width = int(args[0]) if len(args) > 0 else 390
    height = int(args[1]) if len(args) > 1 else 844
    out = args[2] if len(args) > 2 else ''
    httpd, port = serve()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={'width': width, 'height': height},
                            device_scale_factor=2 if width <= 500 else 1)
            pg.goto(f'http://127.0.0.1:{port}/index.html', wait_until='networkidle')
            pg.wait_for_timeout(1600)
            print(json.dumps(pg.evaluate(MEASURE), ensure_ascii=False))
            if out:
                pg.screenshot(path=os.path.join(WS, out), full_page=True)
                print('saved', out)
            b.close()
    finally:
        httpd.shutdown()


if __name__ == '__main__':
    main()
