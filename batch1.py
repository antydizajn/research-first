#!/usr/bin/env python3
"""Batch 1: A/B/C na 8 zadaniach x 3 warianty skilli = 24 sesje hermes chat.

Uruchomienie: hermes chat (nie -z), bo -z to oneshot bez wlasnej sesji
zapisanej do scorera. Sprawdzone: -z dziala, ale `hermes chat -Q` daje pelna
sesje z tools.

Warianty:
  A-baseline            brak skilla
  B-skill-expertise     --skills expertise-research-first
  C-skill-deepresearch  --skills deepresearch

Kazda sesja ma ten sam prompt, rozni sie tylko --skills. Zero zmian w configu.
"""
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HOME = pathlib.Path.home()
RF = HOME / "AI/ANTIGRAVITY/WORKSPACE/RESEARCH-FIRST"
PY = str(HOME / ".hermes/hermes-agent/venv/bin/python3")
VENV_BIN = str(HOME / ".hermes/hermes-agent/venv/bin")
ENV = {**os.environ, "PATH": os.environ.get("PATH", "") + ":" + VENV_BIN}

VARIANTS = {
    "A-baseline": [],
    "B-skill-expertise": ["expertise-research-first"],
    "C-skill-deepresearch": ["deepresearch"],
}

PROMPT_SUFFIX = " Odpowiedz krotko, interesuje mnie wylacznie wynik."


def pick_tasks(per_cat=2):
    tasks = json.loads((RF / "taskset.json").read_text(encoding="utf-8"))["tasks"]
    cats = json.loads((RF / "taskset.json").read_text(encoding="utf-8"))["categories"]
    out = []
    for cat in ("LOCAL", "RECALL", "EXTERNAL", "TRAP"):
        picked = [t for t in tasks if t["cat"] == cat][:per_cat]
        for t in picked:
            t = dict(t)
            t["label"] = "TAK" if cats[cat]["label_src_first_required"] else "NIE"
            out.append(t)
    return out


def run_one(task, variant, skills):
    prompt = task["base"] + PROMPT_SUFFIX
    # Skladnia zweryfikowana 2026-09-30 na `hermes --version` i bledzie
    # argparse: NIE MA `hermes chat -Q`. Jest globalne `-z PROMPT`
    # oraz globalne `--skills SKILLS`. Poprzednia wersja uzywala
    # `hermes_cli.main chat -Q` i wszystkie 24 sesje padly z RC=2.
    cmd = [PY, "-m", "hermes_cli.main", "-z", prompt]
    for s in skills:
        cmd += ["--skills", s]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=600, env=ENV)
        rc, err = r.returncode, (r.stderr or "")[-200:]
        out = (r.stdout or "")[:150]
    except subprocess.TimeoutExpired:
        rc, err, out = -9, "TIMEOUT", ""
    return {
        "task_id": task["id"], "cat": task["cat"], "label": task["label"],
        "variant": variant, "skills": skills, "prompt": prompt,
        "rc": rc, "secs": round(time.time() - t0, 1), "out": out, "err": err,
    }


def new_session_ids(before_ids):
    db = HOME / ".hermes/state.db"
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = c.execute("select id from sessions order by started_at desc limit 200").fetchall()
    c.close()
    return [r[0] for r in rows if r[0] not in before_ids]


def main():
    tasks = pick_tasks(per_cat=2)
    plan = [(t, v, s) for t in tasks for v, s in VARIANTS.items()]
    print(f"zadania: {len(tasks)}  warianty: {len(VARIANTS)}  sesje: {len(plan)}",
          flush=True)

    db = HOME / ".hermes/state.db"
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    before = {r[0] for r in c.execute("select id from sessions")}
    c.close()

    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(run_one, t, v, s): (t, v) for t, v, s in plan}
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            results.append(r)
            print(f"  [{i}/{len(plan)}] {r['task_id']:<4} {r['variant']:<20} "
                  f"rc={r['rc']} {r['secs']:>5}s", flush=True)

    ids = new_session_ids(before)
    print(f"\nnowych sesji w state.db: {len(ids)}  czas: {time.time()-t0:.0f}s")
    (RF / "_batch1_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    (RF / "_batch1_sessions.json").write_text(
        json.dumps(ids, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(1 for r in results if r["rc"] == 0)
    print(f"rc=0: {ok}/{len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
