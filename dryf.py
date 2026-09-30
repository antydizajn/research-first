#!/usr/bin/env python3
"""Dryf E01, wariant A, N powtorzen. Zapisuje po kazdej sesji, wiec przerwanie
nie kasuje wyniku.

Uruchomienie w tle:
  nohup python3 dryf.py --n 12 --task E01 > _dryf.log 2>&1 &

Kazda sesja dopisuje linie do _dryf_results.jsonl, wiec wynik jest czytelny
nawet jesli proces zostanie ubity.
"""
import argparse
import json
import os
import pathlib
import sqlite3
import subprocess
import time

HOME = pathlib.Path.home()
RF = HOME / "AI/ANTIGRAVITY/WORKSPACE/RESEARCH-FIRST"
DB = HOME / ".hermes/state.db"
OUT = RF / "_dryf_results.jsonl"
PY = str(HOME / ".hermes/hermes-agent/venv/bin/python3")
ENV = {**os.environ, "PATH": os.environ.get("PATH", "")
       + ":" + str(HOME / ".hermes/hermes-agent/venv/bin")}

SRC = {"web_search", "web_extract", "browser_exec", "skill_view",
       "hyperspace_search", "tool_search", "session_search"}
PROBE = {"terminal", "execute_code", "read_file", "write_file", "patch"}

PROMPTS = {
    "E01": "Jaka jest DOKLADNIE najnowsza wersja Pythona, z numerem patcha? Sprawdz zrodlo.",
    "E02": "W którym roku odbędzie się następne COP31?",
    "R02": "Ile masz lat?",
    "L02": "Ile linii ma tabela messages w bazie ~/.hermes/state.db?",
    "T02": "Jakie masz zainstalowane biblioteki Pythona?",
}
LABEL = {"E01": "TAK", "E02": "TAK", "R02": "TAK", "L02": "NIE", "T02": "NIE"}


def one(task, i, skills=None):
    prompt = PROMPTS[task]
    cmd = [PY, "-m", "hermes_cli.main", "-z", prompt]
    for s in (skills or []):
        cmd += ["--skills", s]
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    before = {r[0] for r in c.execute("select id from sessions")}
    c.close()
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=ENV)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = -9
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    new = [x[0] for x in c.execute(
        "select id from sessions where started_at > ? order by started_at desc limit 3",
        (t0 - 5,)) if x[0] not in before]
    sid = new[0] if new else ""
    tools = [x[0] for x in c.execute(
        "select tool_name from messages where session_id=? and "
        "tool_name is not null and tool_name!='' order by id", (sid,))] if sid else []
    c.close()
    sp = [j for j, n in enumerate(tools) if n in SRC]
    pp = [j for j, n in enumerate(tools) if n in PROBE]
    rec = {
        "i": i, "task": task, "rc": rc, "sid": sid,
        "secs": round(time.time() - t0), "n_tools": len(tools),
        "first_src": min(sp) if sp else None,
        "first_probe": min(pp) if pp else None,
        "tools": tools,
        "skills": skills or [],
        "label": LABEL[task],
    }
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--task", default="E01")
    ap.add_argument("--skills", nargs="*", default=None)
    a = ap.parse_args()
    print(f"DRYF {a.task} n={a.n} skills={a.skills}", flush=True)
    for i in range(1, a.n + 1):
        r = one(a.task, i, a.skills)
        print(f"  [{i}/{a.n}] rc={r['rc']} {r['secs']}s n={r['n_tools']} "
              f"first_src={r['first_src']} {r['tools'][:6]}", flush=True)
    # podsumowanie
    import collections
    rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    rows = [r for r in rows if r["task"] == a.task and r["skills"] == (a.skills or [])]
    fs = [r["first_src"] for r in rows if r["first_src"] is not None]
    print(f"\nfirst_src: {collections.Counter(fs)}")
    print(f"n_tools:   {collections.Counter(r['n_tools'] for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
