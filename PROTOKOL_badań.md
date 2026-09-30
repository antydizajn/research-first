# PROTOKOL BADAŃ: RESEARCH-FIRST

Poligon doswiadczalny. Każda liczba w tym dokumencie pochodzi z odczytu
`~/.hermes/state.db` lub z katalogu na dysku. Zero liczb z pamięci modelu.

Status: v1.0, 2026-09-30, sesja `20260928_164353_75c510`
Metodyka: `evidence-corpus-research`, `deepresearch`, `research-paper-writing`
Instrument nadzoru: `hermes kanban`, tablica `research-first`

---

## 0. OBIEKT EKSPERYMENTU

Obiektem nie jest skill. Obiektem jest **zachowanie**: czy agent sięga po źródło
zanim zacznie działać diagnostycznie.

Interwencja (skill, hook, plugin) jest tylko narzędziem. Jeśli narzędzie nie
zmienia zachowania, jest martwe, niezależnie od tego jak ładnie wygląda.

**Ostateczny artefakt**: jeden metodologicznie opracowany i zbadany artefakt
(`skill` LUB `hook` LUB `plugin`), wdrożony do Hermesa. Nie trzy naraz.

---

## 1. ZMIERZONY STAN STARTOWY (baseline)

Źródło: `~/.hermes/state.db`, odczyt `mode=ro`, 2026-09-30.

```
sesje w bazie                     16 448
wiadomości                    620 897
wywołania narzędzi (tool_name)   314 731
```

Rozkład `tool_name` (top, kanoniczne nazwy):

| narzędzie | liczba | klasa |
|---|---|---|
| `terminal` | 126 113 | PROBE |
| `read_file` | 42 954 | PROBE |
| `patch` | 23 491 | PROBE |
| `execute_code` | 23 212 | PROBE |
| `search_files` | 20 736 | lokalne |
| `skill_view` | 14 850 | SRC |
| `write_file` | 11 667 | PROBE |
| `web_search` | 3 946 | SRC |
| `hyperspace_search` | 2 617 | SRC |
| `web_extract` | 1 198 | SRC |

Sumy klas (przy zdefiniowanych zbiorach):

```
SRC  razem    25 514
PROBE razem  228 269
stosunek     10,05 %
```

**BASELINE (surowy, Historyczny):**

```
sesje z >=1 probe i >=1 src      1 007
sesje z probe ale ZERO src        5 657
W0 rate (probe-first, zero src)  84,89 %
sesje z jakimkolwiek src          2 621
sesje z jakimkolwiek probe        8 115
```

### 1.1 Dlaczego tę liczbę NIE uznaję za efekt

To jest **korelacja obserwacyjna na danych historycznych**, nie eksperyment.
Każda z 8 115 sesji już miała swoją historyczną wartość zmiennej `S`
(stan skilla, obecność hooka, treść promptu). Nie wiem, co by było, gdybym
zmieniła `S` w tej konkretnej sesji. **Nie ma kontrfaktu przeciwfaktu.**

Dodatkowo baseline 84,89% jest **zawyżony jako miara zachowania** i
**zaniżony jako wskaźnik problemu**, z dwóch niezależnych powodów:

1. **Mylące źródła.** `search_files` (20 736 wywołań) NIE jest źródłem
   wiedzy o świecie, jest lokalnym indeksem dysku. Zadanie „znajdź na
   wszystkich dyskach folder niemieczkowo" powinno zostać obsłużone przez
   `find`, a LLM słusznie odpowiedziało `LOKALNIE`. Liczenie tego jako
   fałszywego alarmu reguły jest błędem miary, nie błędem agenta. To
   odkrycie z 2026-09-29, zapisane w CHANGELOGu skilla, i **nierozwiązane**.
2. **Nieoznakowane sesje.** 5 657 sesji z probe i bez src zawiera rozmowy
   „elo", „ok", reply na jedno słowo, persony, benchmarki, crony ROJ. Żadna
   z nich nie powinna wejść do źródła, a mój licznik wymusza na nich
   wniosek.

Dlatego: **84,89% jest punktem odniesienia, nie liczbą do poprawy.**

---

## 2. PROBLEM DO ROZWIĄZANIA

Trzy osobne pytania, które wcześniej były wymieszane:

**P1. Czy reguła zmienia zachowanie?** Wymaga A/B na żywych sesjach.
Offline nie odpowie, bo brak kontrfaktu.

**P2. Która czysta decyzja jest dobra?** Dane historyczne nie mają etykiety
„ta sesja powinna była iść do źródła". **Etykieta musi powstać PRZED
pomiarem**, z ludzkiego osądu, nie z regexu.

**P3. Czy to jest warte kosztu?** Każda interwencja kosztuje tokeny
(system prompt) albo czas (hook per call). Koszt trzeba zmierzyć, nie
oszacować.

---

## 3. PROTOKÓŁ POMIARU

### 3.1 Zbiór zadań (task set)

Tworzę **40 zadań**, w czterech kategoriach po 10:

| kategoria | definicja | oczekiwane zachowanie |
|---|---|---|
| `LOCAL` | odpowiedź jest na dysku | NIE iść do sieci |
| `RECALL` | fakty o Paulinie / projekcie | `hyperspace_search` PRZED odpowiedzią |
| `EXTERNAL` | fakty o świecie spoza dysku | sieć PRZED odpowiedzią |
| `TRAP` | zadanie wyglądające na EXTERNAL, ale rozwiązywalne lokalnie | `search_files`, NIE sieć |

Zadania `TRAP` są najważniejsze. To one odróżniają agenta od **agenta, który
robi wszystko przez sieć**, co jest równie złe jak agent, który nie robi nic
przez sieć.

Każde zadanie dostaje 3 warianty tekstu (parafrazy), żeby sprawdzić, czy
efekt zależy od sformułowania. Razem **120 promptów**.

### 3.2 Etykieta ground truth

Ustalam PRZED uruchomieniem, per kategoria:

```
LOCAL   -> SRC-first = FALSE  (pójście do sieci to błąd)
RECALL  -> SRC-first = TRUE   (musi być hyperspace_search)
EXTERNAL-> SRC-first = TRUE   (musi być web_search lub web_extract)
TRAP    -> SRC-first = FALSE  (sieć to błąd, wystarczy lokal)
```

Etykieta jest funkcją KATEGORII, nie treści odpowiedzi. To eliminacja
najgorszego błędu z mojego pomiaru z 2026-09-29: tam regex powstał PO
obejrzeniu wyników, czyli ground truth pochodził z przecieku. **Tutaj
ground truth poprzedza pomiar i jest funkcją stałą.**

### 3.3 Metryki

Na poziomie sesji:

```
recall      = 1 gdy poprawnie zachowana sesja, 0 gdy nie
precision   = 1 gdy poprawnie zachowana sesja, 0 gdy nie   (ta sama, bo FN i FP sa rozroznialne przez kategorie)
```

Na poziomie pary (agent, zadanie):

```
accuracy  = (TP + TN) / wszystkie
```

Wskaźniki zbiorcze:

```
FBR (false block rate)  = FP / (FP + TN)   -> ile razy niepotrzebnie wezwano do sieci
recall_rate             = TP / (TP + FN)   -> ile razy nie poszlo, a powinno
```

**Próg zabicia ustalam PRZED pomiarem.** Wartość: `FBR <= 0,10` i
`recall_rate >= 0,70`. Jeśli wariant nie przekracza tego progu, wariant
odpada i **nie zmieniam progu pod wynik**. Utrata progu pod wynik to
dokładnie to, przed czym plan ma zabezpieczenie (CHANGELOG 2026-09-29).

### 3.4 Interwencje do porównania

| wariant | co zmienia | koszt |
|---|---|---|
| `A-baseline` | nic, skill 0.5.0 jak jest | 0 |
| `B-skill-v05` | `expertise-research-first` 0.5.0 (jest na dysku) | tokeny w system prompt |
| `C-skill-v06` | wariant iterowany, do napisania | tokeny |
| `D-hook` | NOTICE po probe przez `transform_tool_result` | czas per call |
| `E-plugin` | `research-order`, obecnie wyłączony | czas per call |

**Każdy wariant na tych samych 120 promptów.** Losowy porządek wewnątrz wariantu
żeby kolejność sesji nie była zmienną ukrytą.

---

## 4. REALIZACJA PRZEZ KANBAN

Potwierdzone w kodzie (`hermes_cli/kanban_db_dispatch.py:2749`): dispatcher
przekazuje `--skills X` do workera, a `tools/kanban_tools.py:1082` przyjmuje
`skills=` przy tworzeniu karty.

To znaczy, że **`kanban_create(skills=[...])` jest moim przyciskiem
eksperymentalnym**: ten sam task, inny zestaw skilli, dispatcher robi resztę.

```
hermes kanban create "RF-A-001" --assignee default --skills expertise-research-first
hermes kanban create "RF-A-001" --assignee default
```

Tablica `research-first` już utworzona:
`~/.hermes/kanban/boards/research-first/kanban.db`

**Protokół nadzoru** (`hermes-kanban-supervision`):

- dowodem zakończenia karty jest `kanban_show.status`, nie `rc=0` z procesu
- karta z `block_kind='needs_input'` i `rec=1` to **odrzucona decyzja**, nie
  oczekujący input
- komentarz QA na karcie **wykonawczej**, nie na karcie-matce
- pusty slot z `todo` to graf zależności, nie błąd dispatchera
- `ps` z workerem bez logu: najpierw `find ~/.hermes/kanban -name 't_<id>.log'`

---

## 5. CZEGO NIE BĘDĘ ROBIŁ

| zakaz | dlaczego |
|---|---|
| zmieniać progu pod wynik | plan ma zabezpieczenie, złamałam je raz |
| dopisywać regexu po obejrzeniu wyników | ground truth z przecieku, 2026-09-29 |
| nazywać `search_files` źródłem wiedzy o świecie | 20 736 wywołań, myli lokalne z sieciowym |
| raportować FBR z jednego wariantu jako wynik | 81% i 18,5% to dwa różne warianty tej samej miary |
| włączać bramkę „bo 17/17 testów przechodzi" | testy jednostkowe nie są A/B |
| twierdzić, że artefakt jest gotowy bez realnego A/B | deklaracja to nie przejście stanu |
| używać Palantir do konsultacji | zbanowany 2026-09-11, kategorycznie |

---

## 6. HARMONOGRAM

| faza | co | status |
|---|---|---|
| F0 | baseline zmierzony | **zrobione** (§1) |
| F1 | 40 zadań + 120 promptów + etykiety | **zrobione 2026-09-30** (`POMIAR_F1_zbior_zadan.md`) |
| F2 | wariant A, B na 120 promptów | **blokowane**: patrz §7 punkt 3 i punkt 4 |
| F3 | pomiar, decyzja kill/keep wg progu z §3.3 | do zrobienia |
| F4 | wariant C (iteracja promptu) na podstawie F3 | do zrobienia |
| F5 | hook i plugin, tylko jeśli A/B nie daje wyniku | warunkowo |
| F6 | raport: co działa, co nie, po co | do zrobienia |
| F7 | wdrożenie jednego artefaktu do Hermesa | decyzja Pauliny |

**F5 jest warunkowe.** Jeśli prompt i skill dają mierzalny efekt, hook i plugin
są zbędne i nie buduję ich. To jest decyzja zapobiegająca budowaniu mechanizmu,
którego nie potrzebujemy.

---

## 7. OTWARTE NIEPEWNOŚCI

1. Czy `default` jako jedyny assignee wystarczy do eksperymentu z różnymi
   zestawami skilli. Na `default` jest jeden profil, warianty idą przez
   `--skills`, więc **prawdopodobnie tak**, ale nie sprawdzone w praktyce.
2. Czy 120 promptów × 5 wariantów = 600 sesji zmieści się w rozsądnej sesji
   i rozsądnym budżecie. **Nie wiem**, nie policzyłem.
3. Czy workery kanban w ogóle mają ten sam prompt bazowy co moja sesja.
   Jeśli system prompt workera różni się od mojego, wynik nie jest
   przenoszalny na moje zachowanie. **To jest blokada F2.**

4. **Czy zadania RECALL dają się rozstrzygnąć w pamięci.** `R06` pyta
   o imię psa. Jeśli odpowiedzi nie ma w HSDB, agent pójdzie do sieci i
   dostanie FN, który nie mierzy reguły, tylko lukę w danych. To jest ta
   sama klasa co `search_files` policzone jako źródło. **Trzeba sprawdzić
   10 zadań RECALL przez recall PRZED F2.**

Punkt 3 jest najpoważniejszy. Jeśli worker ma inny prompt bazowy, to
eksperyment na kanban mówi o workerach, nie o mnie. **Trzeba to zmierzyć
przed F2, nie po.**

---

## 8. LOG DECYZJI

| data | decyzja | uzasadnienie |
|---|---|---|
| 2026-09-29 | brama `research-order` odrzucona, FBR 81% regex i 50% LLM | oba powyżej progu 28%, ustalonego przed pomiarem |
| 2026-09-29 | wada miary, nie wariantu | `search_files` policzone jako źródło |
| 2026-09-29 | regex KONTYN unieważniony jako wynik | powstał po obejrzeniu fałszywych alarmów |
| 2026-09-30 | baseline 84,89% zapisany jako punkt odniesienia | korelacja, nie eksperyment |
| 2026-09-30 | kategoria `TRAP` dodana do zbioru zadań | odróżnia dobre zachowanie od „robię wszystko przez sieć" |
| 2026-09-30 | etykieta = funkcja kategorii, nie regex | eliminacja przecieku ground truth |
| 2026-09-30 | próg 0,10 / 0,70 ustalony przed F2 | przesunięcie progu pod wynik = złamana metoda |
| 2026-09-30 | F5 warunkowe | nie buduję mechanizmu, którego nie potrzebuję |
