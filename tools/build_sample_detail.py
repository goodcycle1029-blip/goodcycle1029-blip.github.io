#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""표준 상세 HTML 샘플을 GitHub Pages용 페이지 2개로 만든다.

  python3 tools/build_sample_detail.py

결과 (work/company_site/ 안)
  sample-detail.html       — 고객이 상품을 클릭했을 때 보는 그대로의 상세(업로드 본과 같은 마크업)
  sample-detail-100v.html  — 전기·전자제품에만 자동으로 붙는 ⚡ 100V 변압기 안내 미리보기

원본: downloads/standard_html_sample/detail_sample_upload.html (마켓 업로드용, 이미지 원격 URL)
이 페이지는 폰에서 바로 스크롤해 보도록 이미지를 저장소 안 상대경로로 바꿔 쓴다.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # work/company_site
WS = os.path.dirname(os.path.dirname(ROOT))                                # /workspace
KIT = os.path.join(WS, "downloads/smartstore_kit/smartstore_kit.py")
PRODUCT = os.path.join(WS, "downloads/smartstore_kit/product_bruno_mug.json")
ASSETS = "sample-detail-assets"

HEAD = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#1B365D">
<title>{title}</title>
<style>
  html{{-webkit-text-size-adjust:100%;}}
  body{{margin:0;padding:0;background:#FFFFFF;}}
  img{{max-width:100%;height:auto;}}
</style>
</head>
<body>
"""
TAIL = "\n</body>\n</html>\n"


def load_kit():
    spec = importlib.util.spec_from_file_location("kit", KIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def localize(html: str, product: dict) -> str:
    """이미지 URL → 저장소 상대경로 (파일이 실제로 있는 것만)"""
    mapping = {}
    for i, item in enumerate(product.get("images") or [], 1):
        url = item["url"]
        name = f"sample_{i:02d}.jpg"
        if os.path.exists(os.path.join(ROOT, ASSETS, name)):
            mapping[url] = f"{ASSETS}/{name}"
    for url, rel in mapping.items():
        html = html.replace(f'src="{url}"', f'src="{rel}"')
    return html


def main() -> None:
    kit = load_kit()
    product = json.load(open(PRODUCT, encoding="utf-8"))

    # 1) 고객이 보는 상세 그대로
    frag = kit.build(product)
    bad = kit.lint(frag)
    assert not bad, bad
    frag = localize(frag, product)
    page = HEAD.format(title="브루노 머그 RBHK027 · 상세페이지 표준 샘플 | 굳사이클") + frag + TAIL
    open(os.path.join(ROOT, "sample-detail.html"), "w", encoding="utf-8").write(page)

    # 2) 전기·전자제품일 때만 붙는 100V 안내 미리보기
    v100 = kit.voltage_box({"voltage_100v": True})
    intro = (
        f'<div style="{kit.WRAP}">'
        f'<div style="border-bottom:2px solid {kit.INK};padding:0 0 12px;margin:0 0 18px">'
        f'<div style="font-size:18px;font-weight:800;letter-spacing:0.12em;color:{kit.INK}">'
        f'SAMPLE · 100V BLOCK</div>'
        f'<div style="font-size:18px;color:{kit.SUB};margin:5px 0 0">'
        f'굳사이클 · 일본 구매대행</div></div>'
        f'<div style="font-size:24px;font-weight:800;color:{kit.INK};line-height:1.4;'
        f'letter-spacing:-0.02em;margin:0 0 12px">전기·전자제품에만 자동으로 붙는 안내</div>'
        f'<div style="font-size:19px;line-height:1.62;color:{kit.BLACK};margin:0 0 10px">'
        f'전기포트·밥솥·선풍기처럼 일본 100V 전원을 쓰는 상품의 상세에는 '
        f'아래 붉은 박스가 <b>주문 전 확인 바로 다음</b>에 자동으로 들어갑니다.</div>'
        f'<div style="font-size:19px;line-height:1.62;color:{kit.BLACK}">'
        f'머그컵·도구처럼 전기를 쓰지 않는 상품에는 들어가지 않습니다.</div>'
        f'</div>'
    )
    page2 = (HEAD.format(title="전기제품 전용 · 일본 100V 변압기 안내 미리보기 | 굳사이클")
             + localize(intro, product) + v100 + TAIL)
    open(os.path.join(ROOT, "sample-detail-100v.html"), "w", encoding="utf-8").write(page2)

    print(json.dumps({
        "upload_fragment": "downloads/standard_html_sample/detail_sample_upload.html",
        "pages": ["sample-detail.html", "sample-detail-100v.html"],
        "lint": kit.lint(frag),
        "v100_blocks_main": frag.count('data-block="v100"'),
        "trust_blocks_main": frag.count('data-block="trust"'),
        "ship6_main": frag.count('data-block="ship6"'),
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
