#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1·2호기가 남긴 **대표 알림(ceo_notices)** 을 나미 쪽으로 모은다.

서울 일(`54.116.146.29`)과 도쿄 이(`57.180.156.79`)는 매시간 점검을 마치며
① 대표에게 이득이 되는 정보 ② 놓치면 안 되는 주의사항 ③ PALETTE 음악·유튜브용 소재를
`/opt/gcu/state/ceo_notices.json` 에 구조화해 남긴다. 이 도구가 그것을 읽어
**공개 저장소 밖** 비공개 파일(`../company_site_state/ceo_notices_inbox.json`)에 모으고,
아직 보고하지 않은 항목을 알려 준다. 서버 쪽에서 이미 ID·유사 제목으로 중복을 걸러내고,
여기서도 같은 일이 두 번 보고되지 않도록 `reported` 로 한 번 더 막는다.

쓰는 법
  python3 tools/ceo_notices.py poll              # 두 서버에서 받아 inbox 에 모은다(알림 감지)
  python3 tools/ceo_notices.py check             # 보고 안 한 알림이 있으면 exit 0, 없으면 1
  python3 tools/ceo_notices.py list              # 보고 안 한 알림을 사람이 읽는 형태로
  python3 tools/ceo_notices.py list --all        # 최근 것 전부(보고한 것 포함)
  python3 tools/ceo_notices.py list --json       # 기계가 읽는 형태
  python3 tools/ceo_notices.py ack --all         # 보고를 마친 알림을 내린다
  python3 tools/ceo_notices.py ack <id> [<id>…]  # 지정한 알림만 내린다
  python3 tools/ceo_notices.py digest --hours 24 # 브리핑용 요약(종류별 건수 + 제목)

지키는 선
  · 읽기만 한다(서버 상태 파일을 읽어 오는 것뿐, 마켓·결제·발송 없음).
  · 대표 알림에는 개인정보·계정·서버 주소·큰 금액이 들어가지 않는다(서버가 가림 처리).
    이 파일은 공개 저장소 밖에만 쓴다 — status.json·company.html 로 내보내지 않는다.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from difflib import SequenceMatcher
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.environ.get(
    "GCU_NOTICE_INBOX",
    os.path.join(os.path.dirname(HERE), "company_site_state", "ceo_notices_inbox.json"))
SSH_RUN = os.environ.get("GCU_SSH_RUN", "/workspace/cloud/gcu_seoul_server/ssh_run.py")
TOKYO_SSH_RUN = os.environ.get("GCU_TOKYO_SSH_RUN", "/workspace/cloud/gcu_tokyo_server/ssh_run.py")
TIMEOUT = int(os.environ.get("GCU_NOTICE_TIMEOUT", "90"))
KEEP_DAYS = int(os.environ.get("GCU_NOTICE_KEEP_DAYS", "60"))
MAX_ITEMS = int(os.environ.get("GCU_NOTICE_MAX", "200"))

REMOTE = r'''
import json
try:
    d = json.load(open("/opt/gcu/state/ceo_notices.json"))
except Exception as e:
    d = {"error": "{}: {}".format(type(e).__name__, str(e)[:120])}
print(json.dumps(d, ensure_ascii=False))
'''

KIND_ORDER = {"주의": 0, "이득": 1, "소재": 2}
KIND_LABEL = {"주의": "⚠️ 주의", "이득": "💰 이득", "소재": "🎵 소재"}


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
        return obj if isinstance(obj, dict) else (default or {})
    except Exception:  # noqa: BLE001
        return {} if default is None else default


def save(obj):
    os.makedirs(os.path.dirname(INBOX), exist_ok=True)
    tmp = INBOX + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, INBOX)


def fetch(ssh_run, name):
    """서버의 ceo_notices.json 을 읽어 온다(읽기 전용). 실패해도 예외를 올리지 않는다."""
    try:
        r = subprocess.run([sys.executable, ssh_run, "--stdin", "/opt/gcu/.venv/bin/python -"],
                           input=REMOTE, capture_output=True, text=True, timeout=TIMEOUT)
    except Exception as e:  # noqa: BLE001
        return {"site": name, "ok": False, "error": "{}: {}".format(type(e).__name__, str(e)[:120])}
    line = ""
    for x in (r.stdout or "").strip().splitlines():
        s = x.strip()
        if s.startswith("{") and s.endswith("}"):
            line = s
    if not line:
        return {"site": name, "ok": False,
                "error": (r.stderr or r.stdout or "응답 없음").strip()[:160]}
    try:
        d = json.loads(line)
    except ValueError as e:
        return {"site": name, "ok": False, "error": "JSON 아님: {}".format(str(e)[:100])}
    if d.get("error"):
        return {"site": name, "ok": False, "error": str(d["error"])[:160]}
    return {"site": name, "ok": True, "data": d}


def _similar(a, b, limit=0.72):
    """두 서버가 같은 일을 다른 제목으로 보낸 경우를 잡는다(0.72 이상이면 같은 알림)."""
    A = re.sub(r"\s+", "", str(a or ""))
    B = re.sub(r"\s+", "", str(b or ""))
    if not A or not B:
        return False
    return SequenceMatcher(None, A, B).ratio() >= limit


def merge_inbox(payloads, now=None):
    """서버에서 온 알림을 inbox 에 모은다 — 같은 ID 는 한 번만, 보고 여부는 보존."""
    now = now or datetime.now()
    box = load(INBOX)
    rows = [r for r in (box.get("items") or []) if isinstance(r, dict) and r.get("id")]
    by_id = {r["id"]: r for r in rows}
    added = []
    for p in payloads:
        if not p.get("ok"):
            continue
        for n in ((p.get("data") or {}).get("items") or []):
            if not isinstance(n, dict) or not n.get("id") or not n.get("title"):
                continue
            hit = by_id.get(n["id"])
            if hit is None:
                # 한쪽 서버가 같은 일을 다른 제목으로 보낸 경우도 한 번만 남긴다
                hit = next((r for r in rows if r.get("kind") == n.get("kind")
                            and _similar(r.get("title"), n.get("title"))), None)
            if hit is not None:
                hit["last_at"] = n.get("last_at") or hit.get("last_at")
                hit["hits"] = max(int(hit.get("hits") or 1), int(n.get("hits") or 1))
                continue
            rec = dict(n)
            rec.update({"source_site": p["site"], "seen_at": now.strftime("%Y-%m-%d %H:%M"),
                        "reported": False, "reported_at": ""})
            rows.append(rec)
            by_id[rec["id"]] = rec
            added.append(rec)
    cutoff = (now - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%dT%H:%M")
    rows = [r for r in rows
            if str(r.get("last_at") or r.get("first_at") or r.get("seen_at") or "") >= cutoff
            or not r.get("reported")]
    rows.sort(key=lambda r: (1 if r.get("reported") else 0,
                             KIND_ORDER.get(str(r.get("kind")), 9),
                             str(r.get("first_at") or r.get("seen_at") or "")), reverse=False)
    rows = rows[:MAX_ITEMS]
    box = {"at": now.strftime("%Y-%m-%d %H:%M"),
           "updated_iso": now.isoformat(timespec="seconds"),
           "sites": {p["site"]: {"ok": bool(p.get("ok")), "error": p.get("error", "")}
                     for p in payloads},
           "count": len(rows),
           "pending": sum(1 for r in rows if not r.get("reported")),
           "new_this_poll": [r["id"] for r in added],
           "items": rows,
           "note": "1·2호기가 넘긴 대표 알림 — 보고를 마친 항목은 ack 로 내린다(공개 저장소 밖)"}
    save(box)
    return box, added


def _site_label(r):
    return {"seoul": "서울 일", "tokyo": "도쿄 이"}.get(
        str(r.get("source_site") or r.get("site") or ""), "-")


def pending(box=None, include_reported=False):
    box = box or load(INBOX)
    rows = [r for r in (box.get("items") or []) if isinstance(r, dict) and r.get("id")]
    if not include_reported:
        rows = [r for r in rows if not r.get("reported")]
    rows.sort(key=lambda r: (KIND_ORDER.get(str(r.get("kind")), 9),
                             str(r.get("first_at") or r.get("seen_at") or "")))
    return rows


def fmt_line(r):
    at = str(r.get("first_at") or r.get("seen_at") or "").replace("T", " ")[5:16]
    head = "{} [{}/{}] — {}".format(KIND_LABEL.get(str(r.get("kind")), r.get("kind") or "-"),
                                    r.get("field") or "기타", r.get("urgency") or "참고",
                                    r.get("title") or "")
    out = [head]
    if r.get("detail"):
        out.append("   · " + str(r["detail"]))
    if r.get("action") and str(r["action"]) not in ("참고", "-"):
        out.append("   · 할 일: " + str(r["action"]))
    tail = "   · 근거: {}".format(r.get("source") or "-")
    tail += " · {} {}".format(_site_label(r), at)
    if int(r.get("hits") or 1) > 1:
        tail += " · {}회 확인".format(r.get("hits"))
    out.append(tail)
    return "\n".join(out)


def cmd_poll(args):
    quiet = "--quiet" in args
    payloads = [fetch(SSH_RUN, "seoul"), fetch(TOKYO_SSH_RUN, "tokyo")]
    box, added = merge_inbox(payloads)
    ok_sites = [p["site"] for p in payloads if p.get("ok")]
    bad = [p for p in payloads if not p.get("ok")]
    if not quiet:
        print("[ceo_notices] 서버 응답: " + (", ".join(ok_sites) or "없음")
              + (" · 실패 " + ", ".join("{}({})".format(p["site"], p.get("error", "")[:60]) for p in bad)
                 if bad else ""))
        print("[ceo_notices] 새 알림 {}건 · 보고 대기 {}건 · 보관 {}건".format(
            len(added), box.get("pending", 0), box.get("count", 0)))
        for r in pending(box):
            print(fmt_line(r))
            print()
    if not ok_sites:
        return 2
    return 0


def cmd_check(args):
    box = load(INBOX)
    rows = pending(box)
    if rows:
        print("보고 대기 대표 알림 {}건: {}".format(
            len(rows), " / ".join("[{}] {}".format(r.get("kind"), r.get("title")) for r in rows[:6])))
        return 0
    return 1


def cmd_list(args):
    box = load(INBOX)
    rows = pending(box, include_reported="--all" in args)
    if "--json" in args:
        print(json.dumps({"count": len(rows), "items": rows}, ensure_ascii=False, indent=1))
        return 0
    if not rows:
        print("보고할 새 대표 알림이 없습니다(받은 편지함 {}건).".format(box.get("count", 0)))
        return 1
    for r in rows:
        print(fmt_line(r))
        print()
    return 0


def cmd_ack(args):
    ids = [a for a in args if not a.startswith("-")]
    box = load(INBOX)
    rows = [r for r in (box.get("items") or []) if isinstance(r, dict)]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    hit = 0
    for r in rows:
        if "--all" in args or r.get("id") in ids:
            if not r.get("reported"):
                r["reported"] = True
                r["reported_at"] = now
                hit += 1
    box["items"] = rows
    box["pending"] = sum(1 for r in rows if not r.get("reported"))
    box["at"] = now
    save(box)
    print("[ceo_notices] 보고 완료로 내림 {}건 · 남은 대기 {}건".format(hit, box["pending"]))
    return 0


def cmd_digest(args):
    hours = 24
    if "--hours" in args:
        try:
            hours = int(args[args.index("--hours") + 1])
        except (IndexError, ValueError):
            hours = 24
    box = load(INBOX)
    cut = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M")
    rows = [r for r in (box.get("items") or [])
            if isinstance(r, dict) and str(r.get("first_at") or r.get("seen_at") or "") >= cut]
    if not rows:
        print("최근 {}시간 새 대표 알림 없음 — 두 서버 점검은 정상 범위.".format(hours))
        return 1
    counts = {}
    for r in rows:
        counts[str(r.get("kind") or "-")] = counts.get(str(r.get("kind") or "-"), 0) + 1
    print("최근 {}시간 대표 알림 {}건 — {}".format(
        hours, len(rows), " · ".join("{} {}건".format(k, v) for k, v in counts.items())))
    for k in ("주의", "이득", "소재"):
        part = [r for r in rows if str(r.get("kind")) == k]
        if not part:
            continue
        print("\n[{}]".format(KIND_LABEL.get(k, k)))
        for r in part:
            print(" - ({}/{}) {}{}".format(r.get("field") or "기타", r.get("urgency") or "참고",
                                          r.get("title") or "",
                                          "" if r.get("reported") else " ← 미보고"))
    return 0


COMMANDS = {"poll": cmd_poll, "check": cmd_check, "list": cmd_list,
            "ack": cmd_ack, "digest": cmd_digest}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    fn = COMMANDS.get(cmd)
    if not fn:
        print("모르는 명령: {}\n{}".format(cmd, __doc__))
        return 2
    return fn(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
