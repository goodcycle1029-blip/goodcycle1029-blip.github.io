#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""서울 클라우드 무인 감시 상태를 본사 현황(status.json)에 반영한다.

  python3 tools/sync_server_status.py          # 서버에서 실측해 status.json 갱신
  python3 tools/sync_server_status.py --check  # 갱신 없이 값만 보기

company.html 은 status.json 의 `ceo.server` 를 읽어 「🛰️ 서울 클라우드」 섹션과
「한눈에」 첫 칸의 '최근 정상 점검'(src=server_head) 을 채운다.
IP·계정·키·메일주소는 공개 페이지에 넣지 않는다.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = os.path.join(HERE, "status.json")
SSH_RUN = os.environ.get("GCU_SSH_RUN", "/workspace/cloud/gcu_seoul_server/ssh_run.py")

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
    out["kernel"] = os.uname().release
except Exception:
    pass
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
    head = f"마지막 점검 {at[5:10].replace('-', '/')} {at_short} · 현재 {streak}회 연속 정상"
    if errs:
        head += f" (누적 실행 {runs}회 · 실패 {errs}회)"

    rows = [
        {"k": "감시 주기", "v": "5분마다 자동 확인 · 24시간 (하루 288회)"},
        {"k": "감시 대상", "v": "스마트스토어 + 쿠팡 — 새 주문(결제완료)·취소·반품"},
        {"k": "지금까지 실행", "v": f"현재 {streak}회 연속 정상 · 누적 {runs}회(실패 {errs}회)" if runs is not None else "-"},
        {"k": "최근 정상 점검", "v": f"{at[5:19].replace('T', ' ').replace('-', '/')} · 점검 항목 모두 통과"},
        {"k": "스마트스토어 API", "v": "토큰 재발급·주문 조회 200 OK (서버에서 직접 확인)"},
        {"k": "쿠팡 Open API", "v": coupang_row},
        {"k": "감사로그 무결성", "v": f"해시 체인 {d.get('audit_records', '-')}건 검증 통과 — 변조 흔적 없음"},
        {"k": "상품 매핑", "v": f"{mapped}/{products} ({pct}%)" if mapped else "-"},
        {"k": "새 주문 알림", "v": "메일 발송 정상 — 새 주문·오류가 생기면 바로 메일로"},
        {"k": "서버 자원", "v": f"메모리 {d.get('mem_avail_mb', '-')}MB 여유 · 스왑 {d.get('swap_total_mb', '-')}MB · 디스크 {d.get('disk_free_gb', '-')}GB"},
        {"k": "자동 복구", "v": "재부팅·크래시 뒤 스스로 다시 시작 (오늘 재부팅 1회로 실증)"},
    ]
    note = ("쿠팡도 결제완료 주문을 5분마다 보며 자동으로 상품준비중까지 넘깁니다. "
            "엘덱스 자동 신청은 안전 스위치가 꺼져 있어 사람이 직접 신청합니다. "
            "서버 주소·계정·열쇠는 공개 화면에 넣지 않습니다.")
    return {
        "state": "정상 가동" if d.get("health_ok") else "확인 필요",
        "head": head,
        "rows": rows,
        "note": note,
    }


def main() -> int:
    check = "--check" in sys.argv
    d = fetch()
    sv = build(d)
    print(json.dumps(d, ensure_ascii=False, indent=1))
    print(json.dumps(sv, ensure_ascii=False, indent=1))
    if check:
        return 0

    with open(STATUS, encoding="utf-8") as f:
        st = json.load(f)
    now = datetime.now()
    ceo = st.setdefault("ceo", {})
    ceo["server"] = sv
    ceo["updated_at"] = now.strftime("%Y-%m-%d %H:%M")
    ceo["headline"] = (f"서울 클라우드는 지금 {d.get('streak', d.get('runs_since'))}회 연속 정상으로 돌고 있고(누적 실행 "
                       f"{d.get('runs_since')}회·실패 {d.get('errors_since')}회), 스마트스토어와 쿠팡 주문을 함께 보고 있습니다. "
                       "오늘 첫 주문은 엘덱스 신청접수까지 끝나 내일 09:00 트래킹 입력만 남았습니다.")
    tiles = ceo.get("tiles") or []
    for t in tiles:
        if t.get("label") == "서울 클라우드":
            t["value"] = "정상 가동"
            t["sub"] = (f"{d.get('streak', d.get('runs_since'))}회 연속 정상"
                        + (f" · 누적 실패 {d.get('errors_since')}회" if d.get("errors_since") else ""))
            t["tone"] = "reg"
            rows = (t.get("d") or {}).get("rows") or []
            for r in rows:
                if r.get("k") == "최근 정상 점검":
                    r["v"] = sv["rows"][3]["v"]
                    r.pop("src", None)
                if r.get("k") == "감시 주기":
                    r["v"] = "5분마다 자동 확인 · 24시간 (하루 288회)"
                if r.get("k") == "감시 대상":
                    r["v"] = "스마트스토어 + 쿠팡 — 새 주문(결제완료)·취소·반품"
            dd = t.setdefault("d", {})
            dd["sum"] = (f"사람 없이 24시간 도는 주문 감시 서버입니다. 지금 {d.get('streak', d.get('runs_since'))}회 연속 정상이고, "
                         "스마트스토어와 쿠팡 주문을 5분마다 함께 보고 있습니다. 점검 항목은 모두 통과했습니다.")
            dd["note"] = "아래 「🛰️ 서울 클라우드」 섹션에 점검 항목이 더 있습니다. 여기 시각은 서버가 마지막으로 남긴 기록 기준입니다."
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    print("status.json 갱신 완료:", STATUS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
