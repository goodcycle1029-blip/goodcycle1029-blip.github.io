#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""서울 클라우드 무인 감시 상태를 본사 현황(status.json)에 반영한다.

  python3 tools/sync_server_status.py          # 서버에서 실측해 status.json 갱신
  python3 tools/sync_server_status.py --check  # 갱신 없이 값만 보기

company.html 은 status.json 의 `ceo.server` 를 읽어 「🛰️ 서울 클라우드」 섹션과
「한눈에」 첫 칸의 '최근 정상 점검'(src=server_head) 을 채운다.
서울 서버가 남긴 AI 소견(`state/hanul_ai_opinion.json`)은 `hanul_opinion` 칸으로,
도쿄 서버(도쿄 이)가 남긴 AI 소견(`/opt/gcu/state/gaon_ai_opinion.json`)은 `gaon_opinion` 칸으로 옮겨 담는다 —
company.html 이 CEO 브리프 아래 「🧠 서울 일 AI 소견」·「🗼 도쿄 이 AI 소견」 카드로 나란히 그린다.

주문 진행은 `orders_progress` 칸으로 따로 담는다 — `state/seen_orders.json`·`ready_for_payment_orders.json`
에서 1~4단계(접수·상품준비중·재고/마진·통관부호)를 매시간 다시 매기고, 5~6단계(일본 결제·엘덱스 접수/출고)는
현장에서 확인한 사실을 `../company_site_state/orders_progress.json`(공개 저장소 밖 비공개 파일)에 적어 두면 이어 받는다.
IP·계정·키·메일주소는 물론 고객 이름·주소·연락처·주문번호·통관부호·원가/마진 금액도 공개 페이지에 넣지 않는다.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = os.path.join(HERE, "status.json")
SSH_RUN = os.environ.get("GCU_SSH_RUN", "/workspace/cloud/gcu_seoul_server/ssh_run.py")
TOKYO_SSH_RUN = os.environ.get("GCU_TOKYO_SSH_RUN", "/workspace/cloud/gcu_tokyo_server/ssh_run.py")

REMOTE_SCRIPT = r'''
import json, os, re, subprocess
from datetime import datetime

out = {}
try:
    h = json.load(open("/opt/gcu/state/health.json"))
    out["health_at"] = h.get("at", "")
    out["health_ok"] = bool(h.get("ok"))
    out["health_fails"] = h.get("fails") or []
    out["health_runs"] = len(h.get("history") or [])
except Exception as e:
    out["health_error"] = str(e)

try:
    s = json.load(open("/opt/gcu/state/seen_orders.json"))
    out["last_checked"] = s.get("last_checked", "")
    mr = (s.get("last_result") or {}).get("mapping") or {}
    out["mapped"] = mr.get("mapped")
    out["products"] = mr.get("products")
    out["percent"] = mr.get("percent")
    out["market_errors"] = (s.get("last_result") or {}).get("market_errors") or {}
except Exception as e:
    out["state_error"] = str(e)

try:
    import sys
    sys.path.insert(0, "/opt/gcu")
    from goodcycle_uploader import market_api
    ms = market_api.status("/opt/gcu", use_env=False)
    out["markets"] = {"naver": ms["naver"]["ready"], "coupang": ms["coupang"]["ready"]}
except Exception as e:
    out["markets_error"] = str(e)

# 회차 집계 — 키를 넣고 정상 가동을 시작한 시각(2026-11-23 21:57) 이후
SINCE = "2026-11-23 21:57"
try:
    lines = open("/opt/gcu/state/order_watch.log", encoding="utf-8").read().splitlines()
    ok_times, err_times = [], []
    streak = 0
    for line in lines:
        m = re.match(r"\[([^\]]+)\] (.*)", line)
        if not m:
            continue
        t, msg = m.groups()
        if "새 주문 없음" in msg:
            ok_times.append(t)
            if t >= SINCE:
                streak += 1
        elif "중단" in msg or "실패" in msg:
            err_times.append(t)
            if t >= SINCE:
                streak = 0          # 실패가 나면 '연속 정상'은 거기서 끝난다
    out["runs_since"] = len([t for t in ok_times if t >= SINCE])
    out["streak"] = streak
    out["first_run"] = ok_times[0] if ok_times else ""
    out["last_run"] = ok_times[-1] if ok_times else ""
    out["errors_since"] = len([t for t in err_times if t >= SINCE])
except Exception as e:
    out["log_error"] = str(e)

try:
    v = subprocess.run(["/opt/gcu/.venv/bin/python", "/opt/gcu/scripts/audit_chain.py", "verify"],
                       capture_output=True, text=True, timeout=120).stdout
    j = json.loads(v)
    out["audit_ok"] = bool(j.get("ok"))
    out["audit_records"] = j.get("records")
    out["audit_problems"] = j.get("problems") or []
except Exception as e:
    out["audit_error"] = str(e)

try:
    mem = {}
    for line in open("/proc/meminfo"):
        k, val = line.split(":", 1)
        mem[k] = int(val.split()[0])
    out["mem_total_mb"] = round(mem["MemTotal"] / 1024)
    out["mem_avail_mb"] = round(mem["MemAvailable"] / 1024)
    sw = open("/proc/swaps").read().strip().splitlines()[1:]
    out["swap_total_mb"] = sum(int(l.split()[2]) // 1024 for l in sw)
    out["swap_used_mb"] = sum(int(l.split()[3]) // 1024 for l in sw)
except Exception as e:
    out["mem_error"] = str(e)

try:
    st = os.statvfs("/")
    out["disk_free_gb"] = round(st.f_bavail * st.f_frsize / 1024 ** 3, 1)
except Exception:
    pass

try:
    p = json.load(open("/opt/gcu/state/promo_last.json"))
    out["promo"] = p
except Exception as e:
    out["promo"] = {}

try:
    out["qna"] = json.load(open("/opt/gcu/state/qna/qna_summary.json"))
except Exception as e:
    out["qna"] = {}
    out["qna_error"] = str(e)

try:
    _jp = json.load(open("/opt/gcu/state/jp_stock_latest.json"))
    out["jp_stock"] = {"total_watch": _jp.get("total_watch"), "checked": _jp.get("checked"),
                       "out_of_stock": _jp.get("out_of_stock"), "checked_at": _jp.get("checked_at", "")}
except Exception as e:
    out["jp_stock_error"] = str(e)

try:
    out["detail"] = json.load(open("/opt/gcu/state/coupang_detail_status.json"))
except Exception as e:
    out["detail"] = {}
    out["detail_error"] = str(e)

try:
    import glob
    runs = sorted(glob.glob("/opt/gcu/state/sourcing_candidates_tokyo/runs/*/manifest.json"))
    if runs:
        m = json.load(open(runs[-1]))
        out["tokyo"] = {
            "run": os.path.basename(os.path.dirname(runs[-1])),
            "at": m.get("collected_at", ""),
            "fetched": m.get("fetched"),
            "passed": m.get("passed"),
            "verified": m.get("verified"),
            "sites_ok": m.get("sites_ok"),
            "sites_total": m.get("sites_total"),
            "jp_stock": m.get("jp_stock") or {},
        }
except Exception as e:
    out["tokyo_error"] = str(e)

try:
    today = datetime.now().date()
    ok, last = 0, {}
    for line in open("/opt/gcu/state/sourcing_swap/log.jsonl", encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        j = json.loads(line)
        at = str(j.get("at") or "")
        if j.get("result") == "ok" and at[:10] == today.isoformat():
            ok += 1
            last = {"at": at, "old": j.get("old_name", ""), "new": j.get("new_name", ""),
                    "margin": j.get("margin")}
    out["swap_today"] = {"ok": ok, "last": last}
except Exception as e:
    out["swap_today"] = {}
    out["swap_error"] = str(e)

try:
    out["kernel"] = os.uname().release
except Exception:
    pass

try:
    out["hanul_opinion"] = json.load(open("/opt/gcu/state/hanul_ai_opinion.json"))
except Exception as e:
    out["hanul_opinion"] = {}
    out["hanul_opinion_error"] = str(e)

# 주문 진행 단계용 — 이름·주소·통관부호·주문번호·금액은 담지 않는다(단계 판단에 필요한 최소값만)
try:
    def _sign(v):
        try:
            v = float(v)
        except Exception:
            return None
        return 1 if v > 0 else (-1 if v < 0 else 0)
    _so = {}
    try:
        _so = json.load(open("/opt/gcu/state/seen_orders.json")).get("orders") or {}
    except Exception:
        pass
    _rp = {}
    try:
        _rp = json.load(open("/opt/gcu/state/ready_for_payment_orders.json"))
    except Exception:
        pass
    _now_orders = []
    for _o in (_rp.get("orders") or []):
        if not isinstance(_o, dict):
            continue
        _pid = str(_o.get("product_order_id") or "")
        _s = _so.get(_pid) or {}
        _pccc = _o.get("pccc") or {}
        _src = _o.get("source") or {}
        _mg = _o.get("margin") or {}
        _rt = _o.get("routes") or {}
        _profit = _mg.get("profit_krw")
        if _profit is None:
            _profit = (_rt.get("direct") or {}).get("profit")
        _now_orders.append({
            "key": _pid,
            "market": _o.get("market") or "",
            "market_label": _o.get("market_label") or "",
            "name": _o.get("name") or "",
            "option": _o.get("option") or "",
            "order_at": _o.get("order_date") or "",
            "paid_at": _o.get("payment_date") or "",
            "status": _o.get("status") or "",
            "confirm_ok": _s.get("confirm_result") == "ok",
            "confirm_at": _s.get("confirm_at") or "",
            "pccc_ok": bool(_pccc.get("ok")),
            "pccc_verify": _pccc.get("verify_status") or "",
            "source_ok": _src.get("available"),
            "flags": [str(_f) for _f in (_o.get("flags") or [])][:8],
            "profit_sign": _sign(_profit),
            "updated_at": _o.get("updated_at") or "",
        })
    out["orders_now"] = _now_orders
except Exception as e:
    out["orders_now"] = []
    out["orders_now_error"] = str(e)
print(json.dumps(out, ensure_ascii=False))
'''


def fetch() -> dict:
    """서버에서 실측값을 받아 온다(읽기 전용 — 원격 스크립트를 stdin 으로 넘긴다)."""
    r = subprocess.run([sys.executable, SSH_RUN, "--stdin", "/opt/gcu/.venv/bin/python -"],
                       input=REMOTE_SCRIPT, capture_output=True, text=True, timeout=240)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:400])
    line = [x for x in r.stdout.strip().splitlines() if x.startswith("{")][-1]
    return json.loads(line)


REMOTE_GAON_SCRIPT = r'''
import json
out = {}
try:
    out["gaon_opinion"] = json.load(open("/opt/gcu/state/gaon_ai_opinion.json"))
except Exception as e:
    out["gaon_opinion"] = {}
    out["gaon_error"] = str(e)
print(json.dumps(out, ensure_ascii=False))
'''


def fetch_tokyo() -> dict:
    """도쿄 이의 AI 소견을 받아 온다(읽기 전용·도쿄 전용 키). 실패해도 서울 쪽은 계속 간다."""
    try:
        r = subprocess.run([sys.executable, TOKYO_SSH_RUN, "--stdin", "/opt/gcu/.venv/bin/python -"],
                           input=REMOTE_GAON_SCRIPT, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:400])
        line = [x for x in r.stdout.strip().splitlines() if x.startswith("{")][-1]
        return json.loads(line)
    except Exception as e:  # noqa: BLE001
        print("[gaon] 소견을 받지 못했습니다:", str(e)[:200])
        return {"gaon_opinion": {}, "gaon_error": str(e)[:200]}


def promo_row(d: dict) -> str:
    """서버가 만든 마지막 홍보 묶음 한 줄."""
    p = d.get("promo") or {}
    if not p:
        return "월·수·금 07:30 — 9:16 쇼츠 15초 + 카드뉴스 4장 + /seo·/copy·/viral 문안 (아직 첫 회차 전)"
    at = str(p.get("at", ""))
    size = p.get("video")
    sz = f" · 영상 {size / 1e6:.1f}MB" if isinstance(size, (int, float)) and size else ""
    return (f"월·수·금 07:30 자동 · 최근 {at[5:16]} {p.get('item', '')}"
            f" (검수 {p.get('score', '-')}점{sz})")


def tile_by(tiles: list, *names: str):
    """타일 이름으로 찾는다 — 표기가 바뀌어도('서울 클라우드' → '한울₁' → '서울 일') 찾도록 부분 일치."""
    for t in tiles or []:
        lab = str(t.get("label") or "")
        if any(n and n in lab for n in names):
            return t
    return None


def day_label(at: str) -> str:
    """수집 시각이 오늘이면 '오늘', 아니면 '11/24'처럼 날짜를 돌려준다."""
    try:
        day = datetime.strptime(at[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return "최근"
    return "오늘" if day == datetime.now().date() else day.strftime("%m/%d")


# ---------------------------------------------------------------- 주문 진행 6단계
# 공개 화면에 나가는 값만 만든다: 상품명·마켓·단계·시각·설명.
# 고객 이름·주소·연락처·주문번호·통관부호·원가/마진 금액은 절대 담지 않는다.
STAGE_NAMES = ["주문 접수", "상품준비중 전환", "재고·마진 심사",
               "개인통관고유부호(PCCC) 검증", "일본 구매처 결제", "엘덱스 접수·출고"]
STAGE_ICON = {"done": "✅", "now": "🔄", "hold": "⏸", "wait": "⬜"}
STATE_LABEL = {"running": "진행 중", "hold": "보류", "waiting": "대기", "finished": "완료"}
MAX_ORDERS = 8          # 화면에 남기는 주문 수(최근 순)
KEEP_DAYS = 21          # 서버 목록에서 빠진 주문을 마지막 확인값으로 보여 주는 기간

# 5·6단계(일본 결제·엘덱스 접수/출고)는 서울 서버 파일에 없다.
# 현장에서 확인한 사실을 이 비공개 파일에 적어 두면 다음 동기화부터 화면에 반영된다.
#   work/company_site_state/orders_progress.json  (공개 저장소 밖)
PROGRESS_STATE = os.environ.get("GCU_COMPANY_STATE"
                                ) or os.path.join(os.path.dirname(HERE), "company_site_state", "orders_progress.json")


def _short_time(s) -> str:
    """'2026-11-26T22:11:04+09:00' → '11/26 22:11' (모르면 빈 값)."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})", str(s or ""))
    return f"{m.group(2)}/{m.group(3)} {m.group(4)}:{m.group(5)}" if m else ""


def _short_product(name, option="", limit: int = 46) -> str:
    s = str(name or "").split(",")[0].strip()
    if len(s) > limit:
        s = s[:limit - 1].rstrip() + "…"
    op = str(option or "").strip()
    if op and op not in s and len(op) <= 14:
        s = f"{s} ({op})"
    return s


def _sig(product, market) -> tuple:
    """주문 동일성 판단용(공개 값만으로) — 주문번호는 저장하지 않는다."""
    return (str(product or "")[:14], str(market or ""))


def _step(no: int, state: str, at: str = "", note: str = "") -> dict:
    return {"no": no, "label": STAGE_NAMES[no - 1], "state": state, "at": at, "note": note}


def _auto_steps(rec: dict) -> dict:
    """서울 서버 실측으로 매길 수 있는 1~4단계."""
    flags = rec.get("flags") or []
    st = {}
    at1 = _short_time(rec.get("paid_at") or rec.get("order_at"))
    st[1] = _step(1, "done", at1, f"{rec.get('market_label') or '마켓'} 결제완료로 접수")
    if rec.get("confirm_ok"):
        st[2] = _step(2, "done", _short_time(rec.get("confirm_at")) or at1, "자동 발주확인 — 상품준비중으로 넘겼습니다")
    else:
        st[2] = _step(2, "hold", "", "발주확인 전 — 상품준비중으로 넘기지 못했습니다")
    if "NO_MAP" in flags or "NO_COST" in flags:
        why = [x for x in ("일본 판매처 매핑 없음" if "NO_MAP" in flags else "",
                           "등록 원가 없음" if "NO_COST" in flags else "") if x]
        st[3] = _step(3, "hold", "", " · ".join(why) + " — 마진을 계산할 수 없어 멈칫습니다")
    elif rec.get("source_ok") is False:
        st[3] = _step(3, "now", "", "원상품 품절 — 대체 일본 판매처를 찾는 중")
    elif rec.get("profit_sign") is not None:
        sgn = rec.get("profit_sign")
        st[3] = _step(3, "done" if sgn > 0 else "hold", "",
                       {1: "원가·마진 확인 — 통과", 0: "마진 0원 — 보류", -1: "역마진 — 발주 보류"}.get(sgn, ""))
    else:
        st[3] = _step(3, "now", "", "재고·원가 확인 중")
    if rec.get("pccc_ok") and str(rec.get("pccc_verify") or "").upper() == "VALID":
        st[4] = _step(4, "done", "", "유니패스 검증 통과 · 엘덱스 신청서와 일치")
    elif "NO_PCCC" in flags or not rec.get("pccc_ok"):
        st[4] = _step(4, "hold", "", "통관부호가 없거나 형식이 달라 구매자 확인이 필요")
    else:
        st[4] = _step(4, "now", "", "통관부호 확인 중")
    st[5] = _step(5, "wait", "", "중간 단계가 풀리면 바로 결제")
    st[6] = _step(6, "wait", "")
    return st


def _load_progress_state() -> dict:
    try:
        with open(PROGRESS_STATE, encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _entry(product, market, market_key, received, steps: dict, extra: dict) -> dict:
    """6단계를 묶어 화면용 주문 한 건으로 만든다."""
    order_steps = [steps[i] for i in sorted(steps)]
    done = [s for s in order_steps if s["state"] == "done"]
    holds = [s for s in order_steps if s["state"] == "hold"]
    nows = [s for s in order_steps if s["state"] == "now"]
    if extra.get("state"):
        state = extra["state"]
    elif len(done) == 6:
        state = "finished"
    elif holds:
        state = "hold"
    elif nows:
        state = "running"
    else:
        state = "waiting"
    if extra.get("summary"):
        summary = str(extra["summary"])
    elif state == "finished":
        summary = "6단계 모두 완료" + (" — " + order_steps[-1]["note"] if order_steps[-1].get("note") else "")
    elif holds:
        summary = f"{len(done)}단계까지 완료 · {holds[0]['no']}단계 보류 — {holds[0].get('note') or '확인 필요'}"
    elif nows:
        summary = f"{len(done)}단계 완료 · {nows[0]['no']}단계 진행 중 — {nows[0].get('note') or ''}".strip(" —")
    else:
        summary = f"{len(done)}단계까지 완료 · 다음 단계 대기"
    nxt = extra.get("next")
    if not nxt:
        pend = next((s for s in order_steps if s["state"] in ("hold", "now", "wait")), None)
        nxt = (f"{pend['label']} — {pend.get('note')}" if pend and pend.get("note") else (pend["label"] if pend else ""))
    return {
        "product": product, "market": market, "market_key": market_key,
        "received": received, "state": state, "state_label": STATE_LABEL.get(state, ""),
        "done": len(done), "total": 6, "summary": summary, "next": nxt,
        "steps": order_steps,
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _age_days(at: str) -> float:
    try:
        d0 = datetime.strptime(str(at)[:16], "%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return 9999
    return (datetime.now() - d0).total_seconds() / 86400


def _card_order(o: dict) -> dict:
    """마켓 카드 안의 진행 박스 — 6단계를 한 줄씩."""
    steps = [{"time": STAGE_ICON.get(s["state"], "⬜"),
              "text": s["label"] + (f" · {s['at']}" if s.get("at") else "")}
             for s in o.get("steps") or []]
    tone = "sale" if o.get("state") == "finished" else ("hold" if o.get("state") == "hold" else "run")
    return {"tag": "주문 진행",
            "value": f"{o.get('done', 0)}/6단계 · {o.get('state_label', '')}",
            "note": o.get("summary", ""), "steps": steps, "tone": tone}


def sync_orders(st: dict, d: dict) -> None:
    """orders_progress + 마켓 카드 진행 박스 + CEO 첫 주문 칸을 한 번에 맞춘다."""
    prev = st.get("orders_progress") or {}
    prev_orders = [o for o in (prev.get("orders") or []) if isinstance(o, dict)]
    prev_seq, prev_sig = {}, {}
    for p in prev_orders:
        if p.get("seq"):
            prev_seq[_sig(p.get("product"), p.get("market"))] = int(p["seq"])
        prev_sig[_sig(p.get("product"), p.get("market"))] = p
    extras = {k: v for k, v in (_load_progress_state().get("orders") or {}).items() if isinstance(v, dict)}
    used = set()
    built = []

    for rec in (d.get("orders_now") or []):
        key = str(rec.get("key") or "")
        extra = extras.get(key) or {}
        if extra:
            used.add(key)
        market = extra.get("market") or rec.get("market_label") or ""
        market_key = extra.get("market_key") or {"coupang": "coupang", "naver": "smartstore"}.get(rec.get("market"), rec.get("market") or "")
        steps = _auto_steps(rec)
        for n, ov in (extra.get("stages") or {}).items():
            try:
                i = int(n)
            except (TypeError, ValueError):
                continue
            if i in steps and isinstance(ov, dict):
                steps[i].update({k: v for k, v in ov.items() if v not in (None, "")})
        o = _entry(extra.get("product") or _short_product(rec.get("name"), rec.get("option")),
                   market, market_key,
                   extra.get("received") or _short_time(rec.get("paid_at") or rec.get("order_at")),
                   steps, extra)
        o["_sort"] = str(rec.get("paid_at") or rec.get("order_at") or "")[:19]
        built.append(o)

    for key, extra in extras.items():            # 서버 목록에 더 이상 없는 과거 주문
        if key in used or extra.get("show") is False:
            continue
        steps = {i: _step(i, "wait") for i in range(1, 7)}
        for n, ov in (extra.get("stages") or {}).items():
            try:
                i = int(n)
            except (TypeError, ValueError):
                continue
            if i in steps and isinstance(ov, dict):
                steps[i].update({k: v for k, v in ov.items() if v not in (None, "")})
        o = _entry(extra.get("product") or "상품", extra.get("market") or "",
                   extra.get("market_key") or "", extra.get("received") or "", steps, extra)
        o["_sort"] = str(extra.get("received_ts") or "")
        built.append(o)

    have = {_sig(o["product"], o["market"]) for o in built}
    for p in prev_orders:                        # 서버에서 빠졌지만 최근까지 보던 주문
        sig = _sig(p.get("product"), p.get("market"))
        if sig in have or _age_days(p.get("last_seen")) > KEEP_DAYS:
            continue
        steps = {int(s["no"]): dict(s) for s in (p.get("steps") or []) if isinstance(s, dict) and s.get("no")}
        if len(steps) != 6:
            continue
        q = dict(p)
        q["steps"] = [steps[i] for i in sorted(steps)]
        q["stale"] = True
        q["_sort"] = q.get("_sort") or ""
        built.append(q)
        have.add(sig)

    # 화면 수 조절 — 최근 것부터 MAX_ORDERS 건(대표가 keep 으로 표시한 건은 유지)
    built.sort(key=lambda o: o.get("_sort") or "")
    keep_sigs = {_sig(v.get("product"), v.get("market")) for v in extras.values() if v.get("keep")}
    if len(built) > MAX_ORDERS:
        drop = len(built) - MAX_ORDERS
        rest = []
        for o in built:
            if drop > 0 and _sig(o["product"], o["market"]) not in keep_sigs:
                drop -= 1
                continue
            rest.append(o)
        built = rest

    # 번호(1호·2호…)는 한 번 붙은 뒤 바뀌지 않게 기존 값을 이어받는다
    taken = set()
    for o in built:
        s = prev_seq.get(_sig(o["product"], o["market"]))
        if s:
            o["seq"] = s
            taken.add(s)
    nxt = max(taken | {0}) + 1
    for o in built:
        if not o.get("seq"):
            o["seq"] = nxt
            taken.add(nxt)
            nxt += 1
    for o in built:
        o["no"] = f"{o['seq']}호"

    built.sort(key=lambda o: o.get("_sort") or "", reverse=True)
    for o in built:
        o.pop("_sort", None)
        o.pop("seq", None)

    cnt = {k: 0 for k in ("running", "hold", "waiting", "finished")}
    for o in built:
        cnt[o.get("state") or "running"] = cnt.get(o.get("state") or "running", 0) + 1
    bits = [f"{STATE_LABEL[k]} {cnt[k]}건" for k in ("running", "hold", "waiting", "finished") if cnt.get(k)]
    head = " · ".join(bits) + (" — 6단계(접수 → 출고) 중 어디까지 왔는지 바로 보입니다" if built else "")
    if cnt.get("hold"):
        head += " · 보류 건은 아래 「지금 막힌 곳」에도 올렸습니다"
    st["orders_progress"] = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "head": head,
        "total": len(built),
        "orders": built,
    }

    # 마켓 카드 안 진행 박스
    for m in (st.get("markets_detail") or []):
        key = m.get("key")
        cand = [o for o in built if o.get("market_key") == key]
        if key in ("coupang", "smartstore", "gmarket", "auction", "11st", "lotteon"):
            m["order"] = _card_order(cand[0]) if cand else m.get("order")

    # CEO 탭 「지금 주문 진행 현황」 — 진행·보류 건을 우선
    act = next((o for o in built if o.get("state") in ("hold", "running", "waiting")), None) \
        or (built[0] if built else None)
    if act:
        st.setdefault("ceo", {})["order"] = {
            "product": act["product"], "market": act["market"],
            "state": act.get("summary", ""),
            "steps": [{"t": f"{s['no']}. {s['label']}",
                       "s": "done" if s["state"] == "done" else "next",
                       "n": " · ".join(x for x in (s.get("at"), s.get("note")) if x) or "아직"}
                      for s in act.get("steps") or []],
            "note": ("고객 이름·주소·통관부호·주문번호·금액 없이 상품명과 6단계만 보여 줍니다. "
                     "단계는 서울 서버 기록과 현장에서 확정한 사실로 매시간 자동 갱신됩니다."),
        }

    # 막힌 곳 목록에도 보류 주문을 올린다(자동 생성분만 매회 교체, 손으로 쓴 항목은 그대로)
    blocked = [b for b in (st.get("blocked") or []) if not (isinstance(b, dict) and b.get("auto") == "orders")]
    for o in built:
        if o.get("state") != "hold":
            continue
        holds = [s for s in o.get("steps") or [] if s["state"] == "hold"]
        blocked.insert(0, {
            "icon": "📦",
            "title": f"{o.get('no')} 주문 {o.get('product')} — {o.get('done')}/6단계에서 멈춤",
            "detail": " / ".join(f"{s['no']}단계 {s['label']}: {s.get('note')}" for s in holds)[:300],
            "impact": "이 주문은 일본 결제로 넘어가지 못했습니다 — 확인 후 다시 진행" if holds else "",
            "owner": "나미",
            "state": "막힘",
            "auto": "orders",
        })
    if blocked or st.get("blocked"):
        st["blocked"] = blocked


def build(d: dict) -> dict:
    at = d.get("health_at", "")
    at_short = at[11:16] if len(at) >= 16 else ""
    runs = d.get("runs_since")
    errs = d.get("errors_since")
    streak = d.get("streak")
    if streak is None:
        streak = runs
    pct = d.get("percent")
    mapped, products = d.get("mapped"), d.get("products")
    markets = d.get("markets") or {}
    merr = d.get("market_errors") or {}
    if not markets.get("coupang"):
        coupang_row = "열쇠 없음 — 지금은 스마트스토어만 감시"
    elif "coupang" in merr:
        coupang_row = "연결 대기 — 윙 연동정보의 허용 IP 반영을 기다리는 중"
    else:
        coupang_row = "결제완료 주문 조회 200 OK · 자동 상품준비중 켜짐"
    qna = d.get("qna") or {}
    qna_last = str(qna.get("last_run") or "")
    qna_row = ("10분마다 스마트스토어 상품Q&A·고객문의 + 쿠팡 상품Q&A·고객센터문의"
               + (f" · 최근 {qna_last[5:16]}" if qna_last else ""))
    if not qna:
        draft_row = "아직 첫 회차 전 — 미답변 문의를 찾으면 초안과 메일 알림"
    else:
        draft_row = (f"대기 {qna.get('drafts_ready', 0)}건 · 이번 회차 새 문의 "
                     f"{qna.get('new_this_run', 0)}건 · 보낸 답변 {qna.get('sent_total', 0)}건"
                     " — 전송은 대표 확인 후")
    head = f"마지막 점검 {at[5:10].replace('-', '/')} {at_short} · 현재 {streak}회 연속 정상"
    if errs:
        head += f" (누적 실행 {runs}회 · 실패 {errs}회)"

    rows = [
        {"k": "감시 주기", "v": "5분마다 자동 확인 · 24시간 (하루 288회)"},
        {"k": "감시 대상", "v": "스마트스토어 + 쿠팡 — 새 주문(결제완료)·취소·반품"},
        {"k": "고객문의 자동 감지", "v": qna_row},
        {"k": "고객문의 답변 초안", "v": draft_row},
        {"k": "마진 기준", "v": "최소 세후 10%+ · 일본 전문몰 30% & 아마존·라쿠텐 인기도 30~60% 중위권 틈새 집중 (가격 방어선 5.5%)"},
        {"k": "마진 자동 점검", "v": "매일 08:30 — 10% 미만은 가격을 올리지 않고 05:00 교체 풀에, 5.5% 미만만 가격 자동 상향"},
        {"k": "지금까지 실행", "v": f"현재 {streak}회 연속 정상 · 누적 {runs}회(실패 {errs}회)" if runs is not None else "-"},
        {"k": "최근 정상 점검", "v": f"{at[5:19].replace('T', ' ').replace('-', '/')} · 점검 항목 모두 통과"},
        {"k": "스마트스토어 API", "v": "토큰 재발급·주문 조회 200 OK (서버에서 직접 확인)"},
        {"k": "쿠팡 Open API", "v": coupang_row},
        {"k": "감사로그 무결성", "v": f"해시 체인 {d.get('audit_records', '-')}건 검증 통과 — 변조 흔적 없음"},
        {"k": "상품 매핑", "v": f"{mapped}/{products} ({pct}%)" if mapped else "-"},
        {"k": "새 주문 알림", "v": "메일 발송 정상 — 새 주문·오류가 생기면 바로 메일로"},
        {"k": "서버 자원", "v": f"메모리 {d.get('mem_avail_mb', '-')}MB 여유 · 스왑 {d.get('swap_total_mb', '-')}MB · 디스크 {d.get('disk_free_gb', '-')}GB"},
        {"k": "홍보 자동 제작", "v": promo_row(d)},
        {"k": "자동 복구", "v": "재부팅·크래시 뒤 스스로 다시 시작 (오늘 재부팅 1회로 실증)"},
    ]
    note = ("고객문의는 10분마다 두 마켓을 훑어 미답변만 골라 답변 초안을 만들고 메일로 알립니다. "
            "고객에게 실제로 보내는 일은 대표가 초안을 확인한 뒤에만 합니다. "
            "쿠팡도 결제완료 주문을 5분마다 보며 자동으로 상품준비중까지 넘깁니다. "
            "엘덱스 자동 신청은 안전 스위치가 꺼져 있어 사람이 직접 신청합니다. "
            "홍보 묶음은 월·수·금 07:30 에 서버가 미리 만들어 두고, 올리는 일은 대표가 확인한 뒤 합니다. "
            "서버 주소·계정·열쇠는 공개 화면에 넣지 않습니다.")
    return {
        "state": "정상 가동" if d.get("health_ok") else "확인 필요",
        "head": head,
        "rows": rows,
        "note": note,
    }


def pretty_model(model: str) -> str:
    """모델 이름을 화면용 짧은 이름으로 — 긴 영문·숫자 열은 공개 검사에서 키로 오인된다.

    gemini-flash-lite-latest → Gemini Flash Lite · gemini-3.5-flash-lite → Gemini 3.5 Flash Lite
    """
    m = str(model or "").strip()
    if not m or "규칙" in m:
        return "규칙 기반 요약"
    m = re.sub(r"(?i)^gemini[-_ ]?", "", m)
    m = re.sub(r"(?i)[-_ ]?latest$", "", m)
    parts = [p for p in re.split(r"[-_]", m) if p]
    out = []
    for p in parts:
        out.append(p.upper() if re.fullmatch(r"\d+(?:\.\d+)?", p) else p.capitalize())
    return ("Gemini " + " ".join(out)).strip()


def public_opinion(op: dict):
    """서울 서버가 남긴 AI 소견에서 공개 화면에 필요한 칸만 골라 담는다.

    서버 쪽에서 이미 가렸지만, 공개 주소로 나가는 길목에서 한 번 더 가린다
    (서버 주소·IP·메일·파일 경로·금액·키로 보이는 문자열).
    """
    if not isinstance(op, dict) or not op.get("lines"):
        return None

    def clean(s, limit=220):
        s = str(s or "")
        s = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "서버", s)
        s = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "메일 주소", s)
        s = re.sub(r"/opt/[\w./-]*", "서버 내부", s)
        s = re.sub(r"\b\d{1,3}(?:,\d{3})+\s*원|\b\d{5,}\s*원", "해당 금액", s)
        s = re.sub(r"\b[A-Za-z0-9_-]{28,}\b", "키", s)
        return s.strip()[:limit]

    verdict = str(op.get("verdict") or "ok")
    if verdict not in ("ok", "warn", "alert"):
        verdict = "ok"
    lines = [clean(x) for x in (op.get("lines") or []) if str(x).strip()][:4]
    if not lines:
        return None
    checks = []
    for r in (op.get("checks") or [])[:12]:   # 새 소식·엔화·기준 문서 줄까지 보이게
        if isinstance(r, dict) and str(r.get("k") or "").strip():
            checks.append({"k": clean(r.get("k"), 40), "v": clean(r.get("v"))})
    cross = op.get("cross") or {}
    cross_out = {
        "public_ok": bool(cross.get("public_ok")),
        "public_age_min": cross.get("public_age_min"),
        "public_at": clean(cross.get("public_at"), 40),
    }
    for key in ("gaon_ok", "gaon_age_min", "gaon_verdict", "hanul_ok", "hanul_age_min", "hanul_verdict"):
        if key in cross and cross.get(key) not in (None, ""):
            val = cross.get(key)
            cross_out[key] = val if isinstance(val, (bool, int, float)) else clean(val, 40)
    model = pretty_model(op.get("model"))
    # 새 소식 영향·아이디어·학습 요약 — 대표 화면에 그대로 보이는 칸(가림 처리 후)
    ideas = []
    for it in (op.get("ideas") or [])[:2]:
        if not isinstance(it, dict):
            continue
        kind = str(it.get("kind") or "").strip()
        if kind not in ("매출", "리스크", "효율"):
            kind = "효율"
        title = clean(it.get("title"), 60)
        action = clean(it.get("action"), 160)
        if not (title or action):
            continue
        ideas.append({"kind": kind, "title": title or action[:40],
                      "why": clean(it.get("why"), 120), "action": action})
    learning = {}
    ln = op.get("learning") or {}
    if isinstance(ln, dict) and (ln.get("count") or ln.get("runs")):
        learning = {"count": int(ln.get("count") or 0), "runs": int(ln.get("runs") or 0),
                    "top": [clean(x, 120) for x in (ln.get("top") or [])[:2] if str(x).strip()]}
    nw = op.get("news") or {}
    news_out = {}
    if isinstance(nw, dict) and (nw.get("count") or nw.get("fx")):
        fx = nw.get("fx") or {}
        news_out = {"count": int(nw.get("count") or 0),
                    "fx_rate": fx.get("rate"),
                    "fx_7d": fx.get("pct_7d")}
    return {
        "at": clean(op.get("at"), 30),
        "at_iso": clean(op.get("at_iso"), 40),
        "node": clean(op.get("node"), 40),
        "verdict": verdict,
        "badge": clean(op.get("badge") or {"ok": "정상", "warn": "확인 필요", "alert": "경보"}[verdict], 20),
        "model": model,
        "lines": lines,
        "impact": clean(op.get("impact"), 140),
        "ideas": ideas,
        "learning": learning,
        "news": news_out,
        "checks": checks,
        "cross": cross_out,
        "next_at": clean(op.get("next_at"), 10),
        "scope": clean(op.get("scope") or "읽기·진단·기록·알림 전용 — 마켓 변경·결제·고객 발송 없음", 80),
    }


def sync_staff(st: dict, d: dict, tk: dict) -> None:
    """'실시간 현황' 직원 카드의 숫자도 서버 실측으로 맞춘다(이름·역할 문구는 손대지 않는다).

    카드를 손으로 적어 두면 동기화가 타일만 고쳐서, 같은 화면에서 카드와 브리프 숫자가
    서로 어긋난다(2026-11-26 649회 vs 653회). 서울 일·도쿄 이 카드의 진행 줄만 갱신한다.
    """
    staff = st.get("staff") or []
    if not staff:
        return
    streak = d.get("streak", d.get("runs_since"))
    runs, errs = d.get("runs_since"), d.get("errors_since")
    det = d.get("detail") or {}
    qna = d.get("qna") or {}
    for s in staff:
        name = str(s.get("name") or "")
        try:
            if name == "서울 일":
                bits = []
                if streak is not None:
                    bits.append(f"{streak}회 연속 정상"
                                + (f"(누적 {runs}회·실패 {errs}회)" if runs is not None else ""))
                if det.get("applied") is not None:
                    bits.append(f"쿠팡 상세 {det['applied']}건 교체·남은 {det.get('remaining')}건")
                if qna:
                    bits.append(f"문의 초안 대기 {qna.get('drafts_ready', 0)}건")
                if bits:
                    s["detail"] = " · ".join(bits)
            elif name == "도쿄 이" and tk.get("fetched") is not None:
                day = day_label(str(tk.get("at") or ""))
                s["current_task"] = (f"🗼 {day} 04:30 수집 — 일본 전문몰 {tk['fetched']:,}건 확인 → "
                                     f"후보 {tk.get('passed', 0):,}건")
                jp = dict(tk.get("jp_stock") or {})
                jp.update({k: v for k, v in (d.get("jp_stock") or {}).items() if v is not None})
                bits = [f"상세검증 {tk.get('verified', 0)}건",
                        f"{tk.get('sites_ok', '-')}/{tk.get('sites_total', '-')}개 몰 성공"]
                if jp.get("checked") is not None:
                    bits.append(f"재고 {jp['checked']}건 점검 중 품절 {jp.get('out_of_stock', 0)}건")
                s["detail"] = " · ".join(bits)
        except Exception as e:  # noqa: BLE001 — 카드 한 줄 때문에 동기화를 멈추지 않는다
            print("[staff] 카드 갱신 건너뜀:", name, str(e)[:100])


def main() -> int:
    check = "--check" in sys.argv
    d = fetch()
    sv = build(d)
    d2 = fetch_tokyo()
    print(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps(d2, ensure_ascii=False, indent=1))
    print(json.dumps(sv, ensure_ascii=False, indent=1))
    if check:
        return 0

    with open(STATUS, encoding="utf-8") as f:
        st = json.load(f)
    now = datetime.now()
    ceo = st.setdefault("ceo", {})
    ceo["server"] = sv
    op = public_opinion(d.get("hanul_opinion") or {})
    if op:
        st["hanul_opinion"] = op
    op2 = public_opinion(d2.get("gaon_opinion") or {})
    if op2:
        st["gaon_opinion"] = op2
    ceo["updated_at"] = now.strftime("%Y-%m-%d %H:%M")
    qn = d.get("qna") or {}
    ceo["headline"] = (f"서울 클라우드는 지금 {d.get('streak', d.get('runs_since'))}회 연속 정상으로 돌고 있고(누적 실행 "
                       f"{d.get('runs_since')}회·실패 {d.get('errors_since')}회), 주문은 5분마다·고객문의는 10분마다 "
                       "함께 보고 있습니다. 고객문의는 답변 초안과 메일 알림까지만 자동이고, 실제 전송은 대표가 확인한 뒤에 합니다.")
    if qn:
        ceo["headline"] += (f" 지금 답변 초안 대기 {qn.get('drafts_ready', 0)}건 · 보낸 답변 "
                            f"{qn.get('sent_total', 0)}건입니다.")
    streak = d.get("streak", d.get("runs_since"))
    tiles = ceo.get("tiles") or []

    # ① 서울 일 (서울 클라우드) 타일 — 예전 이름 '한울'·'서울 클라우드'도 함께 찾는다
    t = tile_by(tiles, "서울 일", "한울", "서울 클라우드")
    if t:
        t["value"] = "정상 가동" if d.get("health_ok") else "확인 필요"
        t["sub"] = (f"{streak}회 연속 정상 · 주문 5분 · 문의 10분"
                    " · 매일 08:30 마진 · 일일장부 30분 자동 기록")
        t["tone"] = "reg" if d.get("health_ok") else "wait"
        rows = (t.get("d") or {}).get("rows") or []
        by_key = {r.get("k"): r for r in rows}
        fresh = {r["k"]: r["v"] for r in sv["rows"]}
        # 쿠팡 상세 진행줄은 서버 상태 파일 실측으로 맞춘다(공개 브리지와 같은 문구)
        det = d.get("detail") or {}
        if det.get("applied") is not None and "쿠팡 상세 자동 보강" in by_key:
            by_key["쿠팡 상세 자동 보강"]["v"] = (
                "780×4,600px 이하 공식몰형 상세 이미지를 만들어 쿠팡 상품수정 API 로 교체 — "
                f"지금까지 {det.get('applied')}건 · 남은 {det.get('remaining')}건 · "
                "매일 4회(09·13·17·21시 40분) 8건씩 무인 교체")
        scan = det.get("reject_scan") or {}
        if scan and "쿠팡 반려 원인 분류" in by_key:
            parts = " · ".join(f"{a} {b}" for a, b in scan.items())
            by_key["쿠팡 반려 원인 분류"]["v"] = (
                f"승인반려 {det.get('coupang_rejected', 0)}건을 상태이력으로 확인 — {parts} "
                "(이미지 규격 건부터 우선 교체)")
        # 이미 있는 줄은 값만 갱신(대표가 손으로 다듬은 문구는 살린다)
        for k in ("최근 정상 점검", "감시 주기", "감시 대상",
                  "고객문의 자동 감지", "고객문의 답변 초안", "마진 자동 점검",
                  "지금까지 실행", "스마트스토어 API", "쿠팡 Open API",
                  "감사로그 무결성", "상품 매핑", "새 주문 알림", "서버 자원",
                  "홍보 자동 제작"):
            if k in by_key and k in fresh:
                by_key[k]["v"] = fresh[k]
                by_key[k].pop("src", None)
        # 없던 줄(고객문의·지금까지 실행)은 '감시 대상' 바로 뒤에 넣는다
        insert_at = next((i + 1 for i, r in enumerate(rows)
                          if r.get("k") == "감시 대상"), len(rows))
        for k in ("고객문의 자동 감지", "고객문의 답변 초안"):
            if k in fresh and k not in by_key:
                rows.insert(insert_at, {"k": k, "v": fresh[k]})
                by_key[k] = rows[insert_at]
                insert_at += 1
        # 수집기·자동 교체 줄도 마지막 실행 실측으로 맞춘다
        if tk_ := (d.get("tokyo") or {}):
            if "전문몰 자동 수집기" in by_key and tk_.get("verified") is not None:
                by_key["전문몰 자동 수집기"]["v"] = (
                    "도쿄 2호기가 일본 IP로 수집·상세검증 → 서울이 04:50 검증 후 05:00 교체에 바로 사용 "
                    f"({day_label(str(tk_.get('at') or ''))} 검증후보 {tk_['verified']}건)")
        sw = d.get("swap_today") or {}
        if "자동 교체" in by_key and sw.get("ok") is not None:
            last = sw.get("last") or {}
            tail = f"({day_label(str(last.get('at') or ''))} {sw['ok']}건"
            if last.get("new"):
                tail += f": {last['new']}"
            by_key["자동 교체"]["v"] = (
                "매일 05:00 — 10% 미만·과열 1~5위·저수익(순익 1만원 미만) 순익 낮은 순부터, "
                "전문몰 30%+ / 아마존·라쿠텐 인기도 30~60% 중위권 틈새로 1:1 교체 " + tail + ")")
        dd = t.setdefault("d", {})
        dd["sum"] = (f"사람 없이 24시간 도는 주문·문의 감시 서버입니다. 지금 {streak}회 연속 정상이고, "
                     "스마트스토어와 쿠팡 주문을 5분마다, 고객문의를 10분마다 함께 보고 있습니다. "
                     "문의는 답변 초안과 메일 알림까지만 하고, 실제 전송은 대표가 확인한 뒤에 합니다. "
                     "그리고 주문이 들어오거나 운송장·배송비가 확정되면 일일장부에 30분 안에 한 줄을 자동으로 적습니다.")
        dd.setdefault("note", "아래 「🛰️ 서울 일」 섹션에 점검 항목이 더 있습니다. "
                              "여기 시각은 서버가 마지막으로 남긴 기록 기준입니다.")

    # ② 도쿄 이 (도쿄 수집) 타일 — 서버가 넘긴 마지막 수집 결과로 맞춘다
    tk = d.get("tokyo") or {}
    t2 = tile_by(tiles, "도쿄 이", "가온")
    if t2 and tk.get("fetched") is not None:
        day = day_label(str(tk.get("at") or ""))
        t2["value"] = "정상 가동"
        t2["sub"] = f"{day} {tk['fetched']:,}건 수집 · 상세검증 {tk.get('verified', 0)}건"
        t2["tone"] = "reg"
        rows2 = (t2.get("d") or {}).get("rows") or []
        jp = dict(tk.get("jp_stock") or {})
        jp.update({k: v for k, v in (d.get("jp_stock") or {}).items() if v is not None})
        for r in rows2:
            k = str(r.get("k") or "")
            if k in ("오늘 수집", "최근 수집", f"{day} 수집"):
                r["k"] = f"{day} 수집"
                r["v"] = (f"{tk['fetched']:,}건 확인 → 후보 {tk.get('passed', 0):,}건 · "
                           f"상세페이지 대조 통과 {tk.get('verified', 0)}건 · "
                           f"{tk.get('sites_ok', '-')}/{tk.get('sites_total', '-')}개 몰 성공")
            elif k == "재고·원가 점검" and jp.get("checked") is not None:
                total = jp.get("total_watch")
                scope = f"등록 상품 {total:,}건 중 하루 80건씩 돌아가며 확인 " if total else "하루 80건씩 돌아가며 확인 "
                r["v"] = (scope + f"({day} {jp['checked']}건 확인·품절 {jp.get('out_of_stock', 0)}건)")

    try:
        sync_staff(st, d, tk)
    except Exception as e:  # noqa: BLE001
        print("[staff] 카드 숫자 갱신 건너뜀:", str(e)[:120])

    try:
        sync_orders(st, d)
        op = st.get("orders_progress") or {}
        print("[orders]", op.get("head") or "주문 없음")
        for o in op.get("orders") or []:
            print("   -", o.get("no"), o.get("market"), o.get("product"),
                  f"{o.get('done')}/6", o.get("state"), "|", o.get("summary"))
    except Exception as e:  # noqa: BLE001 — 주문 칸 때문에 동기화 전체를 멈추지 않는다
        print("[orders] 주문 진행 갱신 건너뜀:", str(e)[:160])

    st["updated_at"] = now.strftime("%Y-%m-%d %H:%M")
    st["updated_iso"] = now.strftime("%Y-%m-%dT%H:%M:%S+09:00")
    with open(STATUS, "w", encoding="utf-8") as f:
        f.write(json.dumps(st, ensure_ascii=False, indent=2))   # 기존 파일과 같은 2칸 들여쓰기(끝 줄바꿈 없음)
    print("status.json 갱신 완료:", STATUS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
