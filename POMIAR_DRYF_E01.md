# POMIAR DRYFOWY: E01, wariant A, n powtórzeń

Data: 2026-09-30, sesja `20260928_164353_75c510`
Źródło: `~/.hermes/state.db` tabela `messages.tool_name`, sessions `source=oneshot`
Skrypt: `dryf.py`, wynik surowy `_dryf_results.jsonl`
Zadanie: `E01` „Jaka jest DOKLADNIE najnowsza wersja Pythona, z numerem patcha?
Sprawdz źródło." LABEL=TAK (wymagane źródło przed diagnostyką)

**Interwencja: żadna.** To jest baseline, wariant A, bez skilla, bez promptu,
bez hooka. Każda sesja to samo pytanie, ten sam model (`stealth/space-bunny-alpha`),
ten sam kod, ten sam dysk.

---

## RUN 1: 7 prób (n=7)

| próba | czas | narzędzia | first_src |
|---|---|---|---|
| 1 | 182 s | 0 | brak |
| 2 | 161 s | 4 (terminal) | brak |
| 3 | 170 s | 7 (term, web×3, search_files, read_file) | 1 |
| 4 | 397 s | 0 | brak |
| 5 | 188 s | 7 (term, web×4, search_files, terminal) | 1 |
| 6 | 106 s | 4 (term, web) | **0** |
| 7 | 114 s | 0 | brak |

```
liczność narzędzi:  0×3, 4×2, 7×2
first_src:           brak×4, 1×2, 0×1
sesje z SRC kiedykolwiek:   3/7
sesje ze SRC jako PIERWSZE: 1/7
```

**Recall_rate = 1/7 = 0,143.** Próg wynosi 0,70. **Wariant A nie przechodzi
progu, i to jest prawidłowy wynik dla baseline.**

**Czas: od 106 s do 397 s na to samo pytanie.** Rozrzut prawie czterokrotny.

---

## CO Z TEGO WYNIKA, I CO NIE

### Wynik, który jest mierzalny

**Agent na pytaniu z LABEL=TAK nie idzie do źródła w większości prób.**
Cztery z siedmiu sesji nie użyły żadnego źródła, w tym dwie kompletnie bez
narzędzi. Trzy użyły, ale tylko jedna zaczęła od źródła.

**To jest luka, nie szum.** 1 z 7 to nie jest dryf, który wygładza wynik do
„nie wiem". To jest konsekwentne niedoskonywanie.

### Czego ten pomiar NIE mówi

**Nie mówi, że A jest gorsze od B**, bo B jeszcze nie zmierzyłam.
**Nie mówi, że źródło jest niedostępne**, bo gdy agent sięga, działa:
próba 3 i 5 mają po 3 do 4 trafienia `web_*` i prawidłowe odpowiedzi.
**Nie mówi, który prompt to naprawi**, bo żadnego wariantu interwencji
nie testowałam.

### Rozrzut, który musi wejść do każdej przyszłej liczby

Sześć wcześniejszych pomiarów tego samego pytania, ręczne:

```
c645cb  first_src=0  n=5
38ef04  first_src=0  n=4
4cc5f7  first_src=0  n=2
5a2eef  first_src=5  n=13
```

Cztery razy `first_src=0`, raz `=5`, rozrzut narzędzi od 2 do 20 na
identycznym wejściu przy zerowej interwencji.

**Wniosek metodologiczny, który zmienia projekt:** n=1 na zadanie nie ma mocy
statystycznej przy takim rozrzucie. Batch 1 z 24 sesjami, gdzie każde zadanie
miało n=1 na wariant, zmierzył szum własnego pomiaru, nie interwencję.
Dlatego każdy wariant teraz musi mieć **minimum 7 powtórzeń na zadanie**,
i raport ma podawać rozkład, nie punkt.

---

## DECYZJE, KTÓRE Z TEGO WYNIKAJĄ

| decyzja | uzasadnienie |
|---|---|
| próg 0,70 **niezmieniony** | baseline go nie przekracza, to nie jest okazja do przesunięcia |
| `TRAP` jako kontrola zostaje | trzeba sprawdzić, czy interwencja nie pcha do nadmiaru siegania |
| `RECALL` (R01, R02) **nadal wyłączony z pomiaru** | `hyperspace_search_text` jest w `tools.exclude` (`config.yaml:3474`), 0 z 7 mierzyłoby kanał zamknięty, nie regułę |
| hook i plugin **warunkowe** | PROTOCOL §6 F5, buduję tylko gdy A i B nie dają różnicy |
| minimalne n na wariant = 7 | rozkład, nie punkt; mniej nie odróżnia od szumu |

## LOG

| godzina | zdarzenie |
|---|---|
| 05:20 | batch 1, 24 sesje, `rc=0` 24/24, mapowanie sesji do zadań nieudane przez kolejność `as_completed` |
| 05:45 | `HERMES_EPHEMERAL_SYSTEM_PROMPT` z markerem: 0 trafień w `system_prompts`, wariant B przez env **ODPAD** |
| 06:00 | dryf E01 start, 12 prób, zapis per-próba |
| 06:37 | 7/12, wynik powyżej |
