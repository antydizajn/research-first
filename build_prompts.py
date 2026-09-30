#!/usr/bin/env python3
"""Generuje 120 promptow z taskset.json. Deterministycznie, bez zadnych wyjatkow.

SSOT dla tresci promptow jest taskset.json. Ten skrypt NIE wymysla zadan,
tylko sklada je z szablonow parafraz.

Uzycie:
    python3 build_prompts.py
    -> prompts_120.txt   (jeden prompt na linie, format: <task_id>|<P1|P2|P3>|<label>|<prompt>)

Blokada: jesli liczba wierszy != 120, skrypt konczy sie kodem 1 i nie
pisze pliku. Częsty przypadek cichego rozsypu sie danych.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASKSET = HERE / "taskset.json"
OUT = HERE / "prompts_120.txt"

EXPECTED_TASKS = 40
EXPECTED_PARAPHRASES = ("P1", "P2", "P3")
EXPECTED_PROMPTS = 120

# Slownik zrodla, do ktorego agent powinien siegnac PRZED pierwszym probe.
# Uzywany przez scorera, NIE wstrzykiwany do prompta (patrz TASKSET_120.md
# zasada 1: zadanie nie zawiera nazwy narzedzia).
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


def build() -> list[str]:
    data = json.loads(TASKSET.read_text(encoding="utf-8"))
    tasks = data["tasks"]
    tpl = data["paraphrase_templates"]

    if len(tasks) != EXPECTED_TASKS:
        sys.exit(f"BLAD: {len(tasks)} zadan, oczekiwano {EXPECTED_TASKS}")

    lines = []
    for t in tasks:
        label = "TAK" if data["categories"][t["cat"]]["label_src_first_required"] else "NIE"
        base = t["base"]
        low = base[0].lower() + base[1:]
        for pk in EXPECTED_PARAPHRASES:
            text = tpl[pk].format(base=base, base_lowered=low)
            if "{" in text or "}" in text:
                sys.exit(f"BLAD: nierozwiazany placeholder w {t['id']}/{pk}: {text}")
            lines.append(f"{t['id']}|{pk}|{label}|{t['cat']}|{text}")

    if len(lines) != EXPECTED_PROMPTS:
        sys.exit(f"BLAD: {len(lines)} promptow, oczekiwano {EXPECTED_PROMPTS}")
    return lines


def main() -> int:
    lines = build()
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK  {len(lines)} promptow -> {OUT}")
    from collections import Counter
    c = Counter(l.split("|")[3] for l in lines)
    for k in ("LOCAL", "RECALL", "EXTERNAL", "TRAP"):
        print(f"    {k:<9} {c[k]:>3}   label="
              f"{'TAK' if data_label(k) else 'NIE'}")
    return 0


def data_label(cat: str) -> bool:
    return json.loads(TASKSET.read_text(encoding="utf-8"))["categories"][cat]["label_src_first_required"]


if __name__ == "__main__":
    raise SystemExit(main())
