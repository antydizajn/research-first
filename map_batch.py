#!/usr/bin/env python3
"""Mapuje sesje z batcha do zadan, po czasie OD STARTU procesu.

Problem odkryty 2026-09-30: `hermes -z` zapisuje sesje w state.db dopiero
PO zakonczeniu pracy, czyli `started_at` to moment konca, nie poczatku.
Kolejnosc z `as_completed` w batch1.py jest losowa (rownolegle watki),
wiec nie da sie z niej odczytac ktora sesja ktore zadanie.

Rozwiazanie: zapisujemy `session_id` z CLI przez `--pass-session-id`,
ktory jest w `hermes --version` jako opcja. Batch nastepnicy to uzyje.
Na to teraz rekonstruujemy po przedrostku promptu w tresci wiadomosci.

Uzytkownik: python3 map_batch.py
"""
import json
import os
import pathlib
import sqlite3
import sys
from collections import defaultdict

HOME = pathlib.Path.home()
RF = HOME / "AI/ANTIGRAVITY/WORKSPACE/RESEARCH-FIRST"
DB = HOME / ".hermes/state.db"

SRC = {"web_search", "web_extract", "hyperspace_search", "skill_view",
       "mcp__gniewka_mcp__recall_memory", "mcp_gniewka_mcp_recall_memory",
       "session_search", "skills_list", "tool_search", "tool_describe"}
PROBE = {"terminal", "execute_code", "read_file", "write_file", "patch",
         "browser_exec"}


def sessions_with_prompts(window_s=2400):
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    out = []
    q = """select id, started_at from sessions
           where source='oneshot' order by started_at desc limit 60"""
    for r in c.execute(q):
        # prompt uzytkownika = pierwsza wiadomosc rola user
        first = c.execute(
            "select content from messages where session_id=? and role='user' "
            "order by id limit 1", (r["id"],)).fetchone()
        prompt = (first["content"] if first else "") or ""
        tools = [x[0] for x in c.execute(
            "select tool_name from messages where session_id=? and "
            "tool_name is not null and tool_name!='' order by id", (r["id"],))]
        out.append({"session_id": r["id"], "started_at": r["started_at"],
                    "prompt": prompt[:300], "tools": tools})
    c.close()
    return out


def classify(tools, label):
    sp = [i for i, t in enumerate(tools) if t in SRC]
    pp = [i for i, t in enumerate(tools) if t in PROBE]
    fs = min(sp) if sp else None
    fp = min(pp) if pp else None
    if label == "TAK":
        if fs is None:
            return False, "brak SRC, a label=TAK"
        if fp is None:
            return True, f"SRC@{fs}, brak PROBE"
        return (fs < fp, f"SRC@{fs} vs PROBE@{fp}")
    if fs is None:
        return True, "zero SRC, zgodne z label=NIE"
    return False, f"SRC@{fs} mimo label=NIE"


def match_task(prompt, tasks):
    """Dopasuj sesje do zadania po unikalnym prefiksie tekstu."""
    p = prompt.lower()
    best, best_len = None, 0
    for t in tasks:
        key = t["base"].lower()
        # pierwsze 40 znakow jako sygnatura
        sig = key[:40]
        if sig in p and len(sig) > best_len:
            best, best_len = t, len(sig)
    return best


def main():
    res = json.loads((RF / "_batch1_results.json").read_text(encoding="utf-8"))
    ts = json.loads((RF / "taskset.json").read_text(encoding="utf-8"))
    tasks = ts["tasks"]
    cats = ts["categories"]
    labels = {t["id"]: ("TAK" if cats[t["cat"]]["label_src_first_required"] else "NIE")
              for t in tasks}
    catof = {t["id"]: t["cat"] for t in tasks}
    variantof = {t["prompt"]: t["variant"] for t in res}
    skillsof = {t["prompt"]: t["skills"] for t in res}

    sess = sessions_with_prompts()
    rows = []
    for s in sess:
        t = match_task(s["prompt"], tasks)
        if not t:
            continue
        label = labels[t["id"]]
        ok, why = classify(s["tools"], label)
        # prompt z sesji ma sufiks; wariant szukamy po pelnym prompcie
        v, sk = "?", []
        for r in res:
            if r["prompt"] in s["prompt"]:
                v, sk = r["variant"], r["skills"]
                break
        rows.append({"session_id": s["session_id"], "task_id": t["id"],
                     "cat": catof[t["id"]], "label": label,
                     "variant": v, "skills": sk,
                     "correct": ok, "why": why, "n_tools": len(s["tools"]),
                     "prompt_seen": s["prompt"][:90]})

    # dedup: jeden session_id = jeden wiersz
    seen, ded = set(), []
    for r in rows:
        if r["session_id"] in seen:
            continue
        seen.add(r["session_id"])
        ded.append(r)

    by_v = defaultdict(list)
    for r in ded:
        by_v[r["variant"]].append(r)

    print(f"zmapowano {len(ded)} sesji na zadania\n")
    summary = {}
    for v in ("A-baseline", "B-skill-expertise", "C-skill-deepresearch",
              "?"):
        sub = by_v.get(v, [])
        if not sub:
            continue
        TP = sum(1 for r in sub if r["label"] == "TAK" and r["correct"])
        FN = sum(1 for r in sub if r["label"] == "TAK" and not r["correct"])
        TN = sum(1 for r in sub if r["label"] == "NIE" and r["correct"])
        FP = sum(1 for r in sub if r["label"] == "NIE" and not r["correct"])
        n = len(sub)
        acc = (TP + TN) / n if n else 0
        fbr = FP / (FP + TN) if (FP + TN) else 0.0
        rec = TP / (TP + FN) if (TP + FN) else 0.0
        summary[v] = {"n": n, "TP": TP, "FP": FP, "TN": TN, "FN": FN,
                      "accuracy": round(acc, 4), "fbr": round(fbr, 4),
                      "recall_rate": round(rec, 4)}
        print(f"{v:<22} n={n:<3} TP={TP} FP={FP} TN={TN} FN={FN}  "
              f"acc={acc:.3f} fbr={fbr:.3f} rec={rec:.3f}")

    th = ts["meta"]["kill_thresholds"]
    print(f"\nprogi (niezmienione): fbr<={th['fbr']}  recall>={th['recall_rate']}")
    for v, s in summary.items():
        verdict = "KEEP" if (s["fbr"] <= th["fbr"]
                             and s["recall_rate"] >= th["recall_rate"]) else "ODPAD"
        print(f"  {v:<22} {verdict}")

    (RF / "_batch1_scored.json").write_text(
        json.dumps({"summary": summary, "rows": ded}, ensure_ascii=False,
                   indent=1), encoding="utf-8")
    print(f"\nzapisano _batch1_scored.json ({len(ded)} wierszy)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
