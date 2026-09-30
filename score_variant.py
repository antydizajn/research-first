#!/usr/bin/env python3
"""Scorer F2. Liczy accuracy / FBR / recall_rate dla jednego wariantu.

Nie zawiera progow. Progi sa w taskset.json (meta.kill_thresholds) i ten
skrypt ich NIE przesuwa. Skrypt raportuje, decyzje podejmuje czlowiek.

Zrodlo danych: ~/.hermes/state.db, tabela messages, kolumna tool_calls.
Odczyt read-only. Sesje mapowane przez jawna liste session_id.

Uzycie:
    python3 score_variant.py --sessions s1.json s2.json --variant B-skill-v05
    python3 score_variant.py --board research-first
"""
import argparse
import json
import pathlib
import sqlite3
import sys
from collections import defaultdict

STATE_DB = pathlib.Path.home() / ".hermes/state.db"
HERE = pathlib.Path(__file__).resolve().parent
TASKSET = HERE / "taskset.json"

SRC_TOOLS = {
    "web_search", "web_extract",
    "hyperspace_search", "mcp__gniewka_mcp__recall_memory",
    "mcp_gniewka_mcp_recall_memory",
    "session_search", "skill_view", "skills_list",
    "tool_search", "tool_describe",
}
PROBE_TOOLS = {
    "terminal", "execute_code", "read_file", "write_file", "patch", "browser_exec",
}


def event_order(conn, session_id: str):
    """Zwraca liste (tool_name, target) w kolejnosci id wiadomosci."""
    ev = []
    q = ("select id, tool_calls from messages "
         "where session_id=? and role='assistant' and tool_calls is not null "
         "and tool_calls != '' order by id")
    for _mid, tc in conn.execute(q, (session_id,)):
        try:
            calls = json.loads(tc)
        except Exception:
            continue
        if isinstance(calls, dict):
            calls = [calls]
        for call in calls:
            f = call.get("function", {})
            name = f.get("name")
            if not name:
                continue
            try:
                a = json.loads(f.get("arguments", ""))
            except Exception:
                a = {}
            tgt = (a.get("file_path") or a.get("path")
                   or a.get("command") or a.get("code") or "")
            ev.append((name, str(tgt)[:120]))
    return ev


def classify(ev, label: str) -> tuple[bool, str]:
    """Zwraca (poprawnosc, uzasadnienie).

    LABEL=TAK  -> poprawne gdy SRC pojawi sie PRZED pierwszym PROBE
    LABEL=NIE  -> poprawne gdy w calej sesji nie pojawi sie ZADEN SRC
    """
    src_pos = [i for i, (n, _) in enumerate(ev) if n in SRC_TOOLS]
    probe_pos = [i for i, (n, _) in enumerate(ev) if n in PROBE_TOOLS]
    first_src = min(src_pos) if src_pos else None
    first_probe = min(probe_pos) if probe_pos else None

    if label == "TAK":
        if first_src is None:
            return False, "brak zadnego SRC, a label=TAK"
        if first_probe is None:
            return True, "SRC uzyte, brak PROBE w ogole"
        if first_src < first_probe:
            return True, f"SRC@{first_src} przed PROBE@{first_probe}"
        return False, f"PROBE@{first_probe} przed SRC@{first_src}"
    # LABEL = NIE
    if first_src is None:
        return True, "zero SRC, zgodne z label=NIE"
    return False, f"SRC@{first_src} mimo label=NIE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", nargs="*", default=[],
                    help="pliki JSON z lista {session_id, task_id, label, cat}")
    ap.add_argument("--variant", default="?")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ts = json.loads(TASKSET.read_text(encoding="utf-8"))
    thresholds = ts["meta"]["kill_thresholds"]

    rows = []
    for f in args.sessions:
        rows.extend(json.loads(pathlib.Path(f).read_text(encoding="utf-8")))
    if not rows:
        sys.exit("BLAD: brak plikow --sessions")

    conn = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True)
    TP = FP = TN = FN = 0
    by_cat = defaultdict(lambda: [0, 0])   # kat -> [poprawne, wszystkie]
    details = []

    for r in rows:
        ev = event_order(conn, r["session_id"])
        ok, why = classify(ev, r["label"])
        by_cat[r["cat"]][1] += 1
        if ok:
            by_cat[r["cat"]][0] += 1
        if r["label"] == "TAK":
            TP += ok
            FN += (not ok)
        else:
            TN += ok
            FP += (not ok)
        details.append({**r, "correct": ok, "why": why,
                        "n_events": len(ev)})

    n = TP + FP + TN + FN
    acc = (TP + TN) / n if n else 0.0
    fbr = FP / (FP + TN) if (FP + TN) else 0.0
    rec = TP / (TP + FN) if (TP + FN) else 0.0

    out = {
        "variant": args.variant,
        "n": n,
        "confusion": {"TP": TP, "FP": FP, "TN": TN, "FN": FN},
        "accuracy": round(acc, 4),
        "fbr": round(fbr, 4),
        "recall_rate": round(rec, 4),
        "by_category": {k: {"correct": v[0], "n": v[1],
                            "rate": round(v[0] / v[1], 4)}
                        for k, v in sorted(by_cat.items())},
        "thresholds_used": thresholds,
        "verdict": ("KEEP" if (fbr <= thresholds["fbr"]
                               and rec >= thresholds["recall_rate"])
                    else "ODPAD (przekroczony próg)"),
    }
    report = {"summary": out, "details": details}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding="utf-8")
        print(f"zapisano {args.out}")
    print(text[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
