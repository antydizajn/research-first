#!/usr/bin/env python3
"""Skan RESEARCH-FIRST + kanban. Uruchamiany przez heartbeat co 5 min.

Napisany 2026-09-30, sesja 20260928_164353_75c510. Zrodlo: PROTOKOL_badań.md §6.

Co robi:
  1. stan folderu RESEARCH-FIRST (pliki, rozmiary, mtime)
  2. nowe pliki w WORKSPACE od poprzedniego skanu (delta, nie absolute)
  3. kanban na WSZYSTKICH tablicach (nie tylko aktywnej, bo aktywna bywa pusta
     a inna pełna - nauczone na bledzie 2026-09-29)
  4. aktywne workery (ps z pelnym argv)
  5. dopisuje linie do _skan.jsonl, czyli historia do porownania

Nie uruchamia niczego, nie tworzy kart, nie zmienia configu. Read-only poza
dopisaniem do wlasnego logu.
"""
import glob
import json
import os
import subprocess
import sqlite3
import sys
import time

HOME = os.path.expanduser("~")
RF = os.path.join(HOME, "AI/ANTIGRAVITY/WORKSPACE/RESEARCH-FIRST")
WS = os.path.join(HOME, "AI/ANTIGRAVITY/WORKSPACE")
LOG = os.path.join(RF, "_skan.jsonl")
STATE = os.path.join(RF, "_skan_state.json")
ENV = {**os.environ, "PATH": os.environ.get("PATH", "")
       + ":" + os.path.join(HOME, ".hermes/hermes-agent/venv/bin")}

# katalogi ktore generuja szum (logi ciagle przepisywane), pomijane w delcie
NOISE = ("/kamery/", ".log", "__pycache__", "/.git/", ".DS_Store")


def sh(*args, timeout=90):
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           timeout=timeout, env=ENV)
        return (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return f"ERR {type(e).__name__}"


def folder_state():
    out = []
    for f in sorted(glob.glob(os.path.join(RF, "*"))):
        try:
            st = os.stat(f)
            out.append({"name": os.path.basename(f),
                        "bytes": st.st_size if os.path.isfile(f) else None,
                        "mtime": int(st.st_mtime)})
        except OSError:
            pass
    return out


def workspace_delta(prev: dict):
    """Zwraca pliki nowe/zmienione od poprzedniego skanu. Tylko nowe."""
    now = {}
    for f in glob.glob(os.path.join(WS, "**/*"), recursive=True):
        if any(n in f for n in NOISE):
            continue
        try:
            if os.path.isfile(f):
                now[f] = int(os.path.getmtime(f))
        except OSError:
            pass
    known = prev.get("seen", {})
    new = {k: v for k, v in now.items() if k not in known}
    changed = {k: v for k, v in now.items() if k in known and known[k] != v}
    removed = [k for k in known if k not in now]
    return now, sorted(new.items(), key=lambda x: -x[1])[:15], changed, removed


def kanban_all():
    """Kolumny rozdzielone SPACJAMI, nie znakiem pionowej kreski.

    Wykryte 2026-09-30: hermes kanban boards list uzywa szerokich kolumn
    ze spacjami. Parser oparty o '|' zwracal pusty slownik, czyli skan
    raportowal 'brak tablic' tam, gdzie sa trzy. Rzecz odczytana
    surowo, nie zgadywana.
    """
    out = {}
    for line in sh("hermes", "kanban", "boards", "list").splitlines():
        line = line.replace("●", " ").strip()
        if not line or line.startswith(("SLUG", "Current board", "Switch boards")):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0] != "SLUG":
            slug = parts[0]
            counts = " ".join(parts[2:]) if len(parts) > 2 else "(empty)"
            out[slug] = counts
    workers = [l for l in sh("ps", "-Ao", "pid,etime,command").splitlines()
               if "kanban" in l.lower() and "grep" not in l]
    return out, len(workers)


def main():
    prev = {}
    if os.path.exists(STATE):
        try:
            prev = json.loads(open(STATE).read())
        except Exception:
            prev = {}
    now, new, changed, removed = workspace_delta(prev)

    rf = folder_state()
    boards, nworkers = kanban_all()

    rec = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": int(time.time()),
        "rf_files": len(rf),
        "rf_total_bytes": sum(x["bytes"] or 0 for x in rf),
        "rf_latest": rf[-1]["name"] if rf else None,
        "ws_new": len(new),
        "ws_new_top": [os.path.basename(p) for p, _ in new[:5]],
        "ws_changed": len(changed),
        "ws_removed": len(removed),
        "boards": boards,
        "kanban_workers": nworkers,
    }
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"seen": now}, f)

    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
