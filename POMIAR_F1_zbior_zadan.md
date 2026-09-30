# POMIAR F1: zbiór zadań gotowy

Data: 2026-09-30, sesja `20260928_164353_75c510`
Źródło danych: pliki w `RESEARCH-FIRST/`, walidacja w `prompts_120.txt`

## Co powstało

| plik | B | rola |
|---|---|---|
| `TASKSET_120.md` | 6 040 | opis 40 zadań, 4 kategorie, uzasadnienie TRAP |
| `taskset.json` | 5 167 | **SSOT** treści zadań i masek etykiet |
| `build_prompts.py` | 2 760 | generuje 120 promptów, deterministycznie |
| `prompts_120.txt` | 21 411 | 120 promptów, `id|parafraza|etykieta|kategoria|tekst` |
| `score_variant.py` | 5 398 | liczy accuracy / FBR / recall_rate dla wariantu |

## Wyniki

```
zadania:      40   (LOCAL 10, RECALL 10, EXTERNAL 10, TRAP 10)
parafrazy:     3   (P1 rzetelny, P2 z kontekstem, P3 potoczny)
prompty:     120
```

**Rozkład etykiet** (funkcja kategorii, ustalona PRZED pomiarem):

| kategoria | promptów | LABEL |
|---|---|---|
| LOCAL | 30 | NIE |
| RECALL | 30 | TAK |
| EXTERNAL | 30 | TAK |
| TRAP | 30 | NIE |

## Walidacja wykonana

```
wierszy w prompts_120.txt              120   OK
unikalnych tasków                       40   OK
błędy struktury (5 pól, regexy ID)      0   OK
niespójność etykieta vs kategoria       0   OK
wyciek nazwy narzędzia do prompta       0   OK
negatywne sformułowania                 0   OK
zakazane myślniki (—, –, ‒, ―)          0   OK
```

**Negatywna kontrola** (skrypt musi odmówić):
usunąłem jedno zadanie z kopii `taskset.json`, 39 zamiast 40:
`RC=1`, `BLAD: 39 zadan, oczekiwano 40`. Plik wyjściowy nie został
nadpisany. Blokada działa.

**Scorer na znanych danych.** Uruchomiony na sesji
`20260929_022238_8f35d7` (861 zdarzeń) z etykietami dobranymi ręcznie, żeby
wynik był sprawdzalny ręcznie, nie tylko wyliczony:

```
pierwsze zdarzenie: terminal  @0
skill_view          @55
web_search          @73
```

Etykieta `TAK` (powinno być SRC przed PROBE) daje **FALSE**,
uzasadnienie `PROBE@0 przed SRC@55`. Etykieta `NIE` (nie wolno SRC) też daje
**FALSE**. Oba wyniki zgodne z tym, co widać w danych. Scorer nie kłamie na
przypadku, który umiem sprawdzić ręcznie.

## Progi: niezmienione

Odczyt z `taskset.json`, `meta.kill_thresholds`:

```
fbr         0,10
recall_rate 0,70
```

Skrypt **nie zawiera progów w kodzie**, tylko je wczytuje. Nie ma sposobu,
żeby przesunąć próg pod wynik bez edycji pliku, którą widać w logu decyzji.

## Czego F1 NIE zrobiło

**Nie uruchomiło żadnego wariantu.** F2 wymaga 600 sesji (120 promptów × 5
wariantów) i tego jeszcze nie ruszyliśmy.

**Nie zweryfikowało, że worker kanban ma ten sam system prompt bazowy co ja**
(otwarta niepewność z §7 punkt 3 protokołu). Bez tego wynik na kanbanie
mówi o workerach, a nie o moim zachowaniu. **To jest blokada F2 i trzeba ją
rozwiązać przed uruchomieniem.**

**Nie sprawdziło, czy zadania z kategorii RECALL dają się rozstrzygnąć.**
`R06` pyta o imię psa. Jeśli w pamięci go nie ma, agent pójdzie do sieci i
dostanie FN, który nie mierzy reguły, tylko lukę w danych. To jest ten sam
błąd co `search_files` liczone jako źródło. **Do sprawdzenia przed F2.**

## Log decyzji F1

| decyzja | uzasadnienie |
|---|---|
| `taskset.json` jako SSOT, nie `.md` | dokument i dane nie mogą się rozjechać |
| skrypt odmawia przy złym liczebniku | cichy rozsyp danych to najczęstsza klasa błędu |
| nazwa narzędzia nie w prompcie | inaczej badamy zdolność do wykonania, nie decyzję |
| nazwa narzędzia w osobnym słowniku w skrypcie | prompt jest czysty, scorer ma swoje mapy |
| `TRAP` jako osobna kategoria | odróżnia dobre zachowanie od „robię wszystko przez sieć" |
| progi tylko w JSON, nie w kodzie | brak mechanizmu przesunięcia progu pod wynik |
| walidacja na danych znanych | „instrument weryfikuj na danych znanych, nie nieznanych" |
