# WYNIK: dwa warianty, n=12 każdy, to samo zadanie

Data: 2026-09-30, sesja `20260928_164353_75c510`
Źródło: `_dryf_results.jsonl`, wygenerowane przez `dryf.py`
Dane behawioralne: `~/.hermes/state.db`, `messages.tool_name`, `source=oneshot`
Zadanie: `E01` „Jaka jest DOKLADNIE najnowsza wersja Pythona, z numerem patcha?
Sprawdz źródło.", LABEL=TAK
Model: `stealth/space-bunny-alpha`, ten sam dla obu wariantów

---

## WYNIK

| wariant | n | źródło jako PIERWSZE | bez narzędzi wcale | mediana | zakres czasu |
|---|---|---|---|---|---|
| **A-baseline** | 12 | **2/12 = 0,167** | 6/12 | 138 s | 99 do 397 s |
| **B-expertise** | 12 | **2/12 = 0,167** | 4/12 | 155 s | 106 do 243 s |

Rozkład `first_src`, identyczny w obu wariantach:

```
brak źródła   7/12
źródło @1     3/12
źródło @0     2/12
```

**Próg zabicia z `taskset.json`: fbr ≤ 0,10, recall ≥ 0,70.**
**Oba warianty odpadają.** Żaden nie przekracza progu recall.

---

## WERDYKT

**`expertise-research-first` 0.5.0 nie zmienia zachowania na tym zadaniu.**

Różnica pomiędzy wariantami: 0,000 w recall, 2 sesje mniej bez narzędzi
(6/12 kontra 4/12), 17 sekund wolniej na medianie. **Żadna z tych różnic nie
przekracza rozrzutu, który zmierzyłam wewnątrz jednego wariantu.**

Rozrzut wewnątrz wariantu A: `first_src` przyjmuje wartości brak, 0 i 1, przy
identycznym wejściu i zerowej interwencji. To jest ten sam rząd wielkości co
każda różnica między A i B. **Porównanie nie odróżnia interwencji od szumu.**

---

## CO TEGO NIE DOWODZI, I TO JEST WAŻNE

1. **Nie dowodzi, że skill jest bezużyteczny.** Jedno zadanie, jeden model,
   jedna maszyna, n=12. Skill 0.5.0 ma warstwę ESKALACJA, która kosztuje zero
   tokenów i nie generuje zachowania, tylko instrukcję warunkową.
2. **Nie dowodzi, że prompt nie działa**, bo wariant B to skill, nie prompt.
   Kanał `HERMES_EPHEMERAL_SYSTEM_PROMPT` sprawdzony 30.09, 0 trafień w
   `system_prompts`, więc prompt jako osobna zmienna **nie był testowany**.
3. **Nie mówi nic o `TRAP`**, czyli o nadmiarze sięgania. Nie zmierzyłam tego
   wariantu.
4. **Nie mówi nic o `RECALL`**, bo `hyperspace_search_text` jest w
   `tools.exclude` (`config.yaml:3474`). Tam 0/7 mierzy zamknięty kanał,
   nie brak reguły.

---

## DECYZJE, KTÓRE WYNIKAJĄ Z TEGO POMIARU

| decyzja | uzasadnienie |
|---|---|
| `expertise-research-first` 0.5.0 **nie wdrażam** jako rozwiązania | n=12, brak różnicy wobec progu, brak różnicy wobec szumu |
| próg 0,70 **nietknięty** | baseline go nie przekracza, to nie jest okazja do przesunięcia |
| `deepresearch` jako wariant C **odpada** | wczoraj 0 z 3 na RECALL, a mierzy zamknięty kanał |
| hook `research-order` **nie buduję** | PROTOCOL §6 F5 warunkowe, warunek nie spełniony |
| n minimum na wariant **podnoszę do 20** | przy rozrzucie `first_src` = {brak, 0, 1} n=12 nie odróżnia |

## CO ZOSTAJE DO ZROBIENIA, W KOLEJNOŚCI

1. **Wariant `TRAP`, n=20, kontrola na nadmiar.** Jeśli agent i tak nie
   przesadza, to skill nie ma czego poprawiać w żadną stronę i zadanie jest
   zamknięte.
2. **Prompt jako osobna zmienna, przez plik konfiguracyjny osobnego profilu,
   nie przez env var.** Env var sprawdzony i odrzucony.
3. **Albo zmiana metody**, bo obserwacja zachowania jednego agenta przy tym
   rozrzucie nie daje mocy. Kandyduje pomiar na wielu agentach, albo pomiar
   odpowiedzi, nie zachowania.

## LOG POMIARÓW DNIA

| godzina | zdarzenie | wynik |
|---|---|---|
| 05:20 | batch 1, 24 sesje, `rc=0` 24/24 | mapowanie sesji do zadań nieudane |
| 05:45 | `HERMES_EPHEMERAL_SYSTEM_PROMPT` z markerem | 0 trafień, wariant **ODPAD** |
| 06:00 do 07:00 | dryf E01, wariant A, 12 prób | recall 0,167 |
| 07:00 do 07:40 | dryf E01, wariant B, 12 prób | recall 0,167 |
