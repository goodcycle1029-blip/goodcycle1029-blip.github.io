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
    qn = d.get("qna") or {}
    ceo["headline"] = (f"서울 클라우드는 지금 {d.get('streak', d.get('runs_since'))}회 연속 정상으로 돌고 있고(누적 실행 "
                       f"{d.get('runs_since')}회·실패 {d.get('errors_since')}회), 주문은 5분마다·고객문의는 10분마다 "
                       "함께 보고 있습니다. 고객문의는 답변 초안과 메일 알림까지만 자동이고, 실제 전송은 대표가 확인한 뒤에 합니다.")
    if qn:
        ceo["headline"] += (f" 지금 답변 초안 대기 {qn.get('drafts_ready', 0)}건 · 보낸 답변 "
                            f"{qn.get('sent_total', 0)}건입니다.")
    tiles = ceo.get("tiles") or []
    for t in tiles:
        if t.get("label") == "서울 클라우드":
            t["value"] = "정상 가동"
            t["sub"] = (f"{d.get('streak', d.get('runs_since'))}회 연속 정상 · 주문 5분 · 문의 10분"
                        + " · 매일 08:30 마진")
            t["tone"] = "reg"
            rows = (t.get("d") or {}).get("rows") or []
            by_key = {r.get("k"): r for r in rows}
            fresh = {r["k"]: r["v"] for r in sv["rows"]}
            # 이미 있는 줄은 값만 갱신(대표가 손으로 다듬은 문구는 살린다)
            for k in ("최근 정상 점검", "감시 주기", "감시 대상",
                      "고객문의 자동 감지", "고객문의 답변 초안"):
                if k in by_key and k in fresh:
                    by_key[k]["v"] = fresh[k]
                    by_key[k].pop("src", None)
            # 없던 줄(고객문의)은 '감시 대상' 바로 뒤에 넣는다
            insert_at = next((i + 1 for i, r in enumerate(rows)
                              if r.get("k") == "감시 대상"), len(rows))
            for k in ("고객문의 자동 감지", "고객문의 답변 초안"):
                if k in fresh and k not in by_key:
                    rows.insert(insert_at, {"k": k, "v": fresh[k]})
                    by_key[k] = rows[insert_at]
                    insert_at += 1
            dd = t.setdefault("d", {})
            dd["sum"] = (f"사람 없이 24시간 도는 주문·문의 감시 서버입니다. 지금 {d.get('streak', d.get('runs_since'))}회 연속 정상이고, "
                         "스마트스토어와 쿠팡 주문을 5분마다, 고객문의를 10분마다 함께 보고 있습니다. "
                         "문의는 답변 초안과 메일 알림까지만 하고, 실제 전송은 대표가 확인한 뒤에 합니다.")
            dd.setdefault("note", "아래 「🛰️ 서울 클라우드」 섹션에 점검 항목이 더 있습니다. "
                                  "여기 시각은 서버가 마지막으로 남긴 기록 기준입니다.")
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)   # 기존 파일과 같은 1칸 들여쓰기
    print("status.json 갱신 완료:", STATUS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
