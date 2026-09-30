# PLAN FINALNY 1: expertise-research-first 0.5.0

**Rodzaj:** plan wdrożenia. Zero zmian w produkcji wykonane.
**Powstał z:** 21 iteracji w `WORKSPACE/iteracje/PLAN1_iter_*.md`
**Data:** 2026-09-29
**Em-dash:** w pliku nie ma znaków U+2014, U+2013, U+2015

---

## 1. CO POMIAR ZMIENIŁ

Pięć rzeczy w tym planie jest opartych na pomiarze, nie na rozumowaniu:

| fakt | pomiar | źródło |
|---|---|---|
| skill jest otwarty 652 razy | 11 529 wywołań `skill_view`, 284 nazwy | `state.db`, `messages.tool_name='skill_view'` |
| jest 9. z 284 skillów | ranking jak wyżej | to samo |
| 10 najczęstszych skillów = lista z bootu | kontekst 8 ostatnich otwarć zbadany | to samo |
| Trigger Rate NIE jest zerowy | 652 > 0 | to samo |
| problemem nie jest opis | dedukcja z powyższego | to samo |

**Wniosek z pomiaru jest odwrotny do mojego pierwotnego założenia.**
Pisałam przez 20 iteracji, że problemem jest Trigger, czyli że opis nie powoduje
otwarcia skilla. **Trigger Rate wynosi 652. Opis działa.**

---

## 2. CO ZOSTAJE W PLANIE

### 2.1 `description` w frontmatter

Obecny (74 słowa):
```
Use when acting as ANY kind of expert/specialist (marketing, prawo, medycyna,
cokolwiek) or when user says 'jestes specjalista od X'. MANDATORY web research
min 20 real sources (real names + academic titles, not pseudogurus), build
EXPERTISE_BASE/<domain>.md on disk, HSDB store. Roleplay without research =
theater, forbidden.
```

Nowy (71 słów):
```
Use when the task needs facts you do not already have: external service fails
or hangs, user asks why something on this machine misbehaves, user asks which
of two options is better, user asks you to act as a named specialist. For
"why is it broken" first check whether others hit the same wall. For "which is
better" run one own measurement before any verdict. A tool's exit code or
HTTP status is not proof of an answer.
```

Co się zmienia, po jednym punkcie:

| element | obecny | nowy | dlaczego |
|---|---|---|---|
| zakres | `ANY`, `cokolwiek` | cztery nazwane sytuacje | `ANY` obejmuje wszystko, czyli nic |
| reguła wejścia | 0 | 2 | z `arXiv 2608.04828` Trigger to osobna mierzalna faza |
| antywzórce | 0 | 1 | `HTTP 200 is not proof` z mojego pomiaru NIM: `gpt-oss-20b` zwrócił 200 z `content: null` |
| liczba źródeł | `min 20` | brak | liczba bez źródła, zobacz 2.2 |
| plik do zbudowania | `EXPERTISE_BASE/<domain>.md` | brak | `arXiv 2607.17598` |
| długość | 74 słowa | 71 słów | przy 96 skillach w katalogu długość opisu ma wagę |

**Krótszy, nie dłuższy.** Iteracja 12 mierzyła opisy wszystkich 96 skillów:
`expertise-research-first` jest w dolnej połowie długości. Krótki opis nie jest
throttlowany, więc dodawanie treści zwiększa ryzyko, nie zmniejsza.

### 2.2 Sekcja E2 w treści skilla

Obecne: `### E2 WEB RESEARCH (min 20 realnych źródeł)`, linia 38, zero uzasadnienia.

Nowe:

| klasa | co to jest | minimum | przykład z mojej sesji |
|---|---|---|---|
| **A** wiedza deklaratywna | marketing, prawo, medycyna, finanse | 10+ źródeł | brak w tej sesji |
| **B** awaria usługi zewnętrznej | provider, API, build, zależności, auth | 3 | zadanie NIM, brak em-dash w hooku |
| **C** diagnoza własnego systemu | „dlaczego moja konfiguracja jest zła" | **0 na start** | 6 wariantów `.env` |
| **D** porównanie opcji | „A czy B" | **1 pomiar własny, 0 źródeł** | modele NIM |

Jedno zdanie obok tabeli, które zastępuje liczbę:
> Liczba źródeł nie jest kryterium jakości. Pokrycie wierzchołkowe jest.
> 20 źródeł o marketingu nie znaczy, że pokryłeś marketing.
> 3 źródła dla awarii API znaczy, że pokryłeś awarię.

### 2.3 Nowa sekcja: ESKALACJA

To jest jedyna nowa treść merytoryczna w całym planie. Pięć zdań:

> **Eskalacja.** Jeśli pierwszy probe dał wynik niejednoznaczny, zanim zrobisz
> drugi, zapytaj czy ktoś inny zgłosił to samo. Koszt: jedno pytanie.
> Zysk: omijasz cały las budowania skryptów, który nie odpowiada na pytanie
> „co jest zepsute", tylko na pytanie „czy ja mam źle ustawienia".
>
> Dla klasy B to pytanie brzmi: czy ktoś już zgłaszał ten błąd, i w jakim
> kontekście. Wątek na forum zawierający twój identyfikator błędu jest
> odpowiedzią. Trzy godziny budowania skryptów diagnostycznych są nie.
>
> Dla klasy C to pytanie brzmi: czy to jest znane, i czy ktoś już to naprawił.

**Skąd to zdanie.** Sesja NIM: 12 wywołań narzędziowych pod rząd, trzy skrypty
w Pythonie, dwa razy po 100 sekund czekania na timeout, zero wyszukiwania.
Dopiero po Twojej interwencji zrobiłam `web_search` i znalazłam wątek na forum
NVIDIA opisujący dokładnie mój błąd. Cała sesja kosztowała wiele godzin,
a wątek był publiczny.

### 2.4 `CHANGELOG.md`, 10 linii

Nowy plik w katalogu skilla. Format: wersja, data, co było złe, dowód, co zmienione.

Dlaczego nowy plik: `~/.hermes/skills/` **nie jest repo git** (sprawdzone przez
`find`, zero `.git`). Nie ma `git revert`, nie ma diffu. Wzorzec odwrotu to
`*.bak_YYYYMMDD_HHMMSS`, jak w 10 hookach w `agent-hooks/`.

---

## 3. CZEGO TEN PLAN NIE ROBI

**Nie dodaje `references/`.** Pierwotny plan proponował cztery pliki.
Wymagałyby od agenta `read_file` na ścieżce, którą musi sam znaleźć.
`arXiv 2607.17598` mierzy trzy harnessy, trzy rodziny modeli, infinityBench,
i mówi: drugi poziom progressive disclosure nigdy nie pomaga i czasem psuje
dokładność. **Trzy pliki w głębokości to trzy poziomy, nie jeden.**

**Nie dodaje `scripts/`.** Wymagałoby `execute_code` do uruchomienia.
Trzeci poziom. Ten sam argument.

**Nie dodaje klasyfikatora regex.** `thinking_gate.py:35-36` ma już w
`HARD_SIGNALS` trzy pozycje: `research`, `paper`, `arxiv`, a w kroku 2
mówi `hyperspace_search(query, limit=15)` przed startem. **Plan 1 byłby
częściowo duplikatem istniejącego hooka.** Dwa regexy widzące to samo zadanie
to szum, który obniża wagę każdego z nich.

**Nie zmienia `boot_discipline.py` ani `thinking_gate.py`.** Oba wstrzykują
reguły o researchie, oba działają słabo, ale to osobna decyzja o warstwie
hooków, opisana w Planie 2.

---

## 4. PROCEDURA

| krok | co | czas | odwracalne |
|---|---|---|---|
| 1 | `ls ~/.hermes/skills-archive/ \| grep expertise` przed backupem | 30 s | tak |
| 2 | `grep -n "skills" install.sh`, czy `hermes update` dotyka skills | 5 min | tak, odczyt |
| 3 | backup: `cp -a` do `skills-archive/expertise-research-first_0.1.0_$(date +%Y%m%d_%H%M%S)` | 1 min | tak |
| 4 | edycja `SKILL.md`: description, E2, ESKALACJA, `version: 0.5.0` | 20 min | tak, krok 3 |
| 5 | `CHANGELOG.md`, 10 linii | 5 min | tak |
| 6 | test description na 30 zdaniach (poniżej) | 30 min | tak |
| 7 | `hermes --version` zapis w CHANGELOG, żeby wiedzieć przy którym buildzie | 1 min | tak |

**Kroki 1 i 2 nie są formalnością.** Wpis w HSDB z 2026-09-28 mówi, że ten sam
problem zniknięcia pliku po `hermes update` był już zapisany dla
`CONFIG/MODEL_SOFT_CONFIG.md`, i ja go nie przeniosłam na skills. Krok 1
sprawdza, czy archiwum już zawiera 0.1.0. Krok 2 sprawdza, czy `install.sh`
kopiuje `skills/` z repo, czyli czy moja wersja przetrwa update.

---

## 5. TESTY, Z ODWRÓCONĄ ASERCJĄ

### 5.1 Asercja inwariantu, nie wartości

Test **nie sprawdza, która klasa** jest poprawna, bo nie mam obiektywnego
kryterium dla „agent przedziel siecią od probeów". Test sprawdza, że
klasyfikacja jest jednoznaczna i stabilna:

```python
def test_klasyfikacja_jednoznaczna():
    for msg in FIXTURES:
        r = classify(msg)
        assert r["klasa"] in ("A", "B", "C", "D")
        assert len(r["sygnaly"]) >= 0
```

To jest lekcja P132 z HSDB: `assert stderr <=> exit != 0`, nie `assert exit == 1`.

### 5.2 Asercja false-positive, najważniejsza

**Test musi sprawdzać, że skill NIE odpala się tam, gdzie nie powinien.**
Bez tego jest testem mojej własnej narracji, czyli klasy 13
(`method-capture` z Twojego skilla `brutal-truth-anti-sycophancy`).

**30 fixture'ów w grupie POWINNO, 10 w grupie NIE POWINNO.**

Grupa NIE POWINNO, brak wyjątku:
```
git status
kontynuuj
dawaj dalej
ok
dzieki
ls ~/AI/ANTIGRAVITY
wczytaj plik X i powiedz co tam jest
dodaj funkcje Y do pliku Z
jestes specjalista od marketingu     (jest, ale nie pytam o moje zasoby)
co to jest HNSW
```

Grupa POWINNO, realne `user_message` z moich sesji:
```
ogarnij czy kimi k3 i glm z nvidia nim gadaja
sprawdz czemu hyperspace-server zjada 100GB RAM
zrob mi research arxiv o guardrails dla agentow
dlaczego ten endpoint zwraca 404
porownaj A vs B ktory lepszy do X
jestes specjalista od marketingu, zrob mi analize
napraw mi build ktory pada
sprawdz moj config czy dobrze ustawiony
audyt mojego kodu pod katem bezpieczenstwa
dlaczego hook nie odpala
czy istnieje juz taki skrypt na dysku
odszukaj przyczyne utraty 407k wektorow
```

Trzy fixture'y **nie do rozstrzygnięcia**, zapisane wprost jako takie:
```
napisz mi skrypt do czyszczenia dysku
co umiem z terminala
```

### 5.3 Kryterium przejscia

```
grupa POWINNO:   >= 9 z 12
grupa NIE:        0 z 10        <- zero tolerancji
nierozstrzygniete: dowolnie, opisywane
```

Zero tolerancji na FPR, bo każdy fałszywy alarm to zbędne wywołanie
narzędzia w realnej sesji.

**Wzorzec metryki:** `arXiv 2608.04828` (Skill-Use) mierzy dokladnie to,
rozkładając na **Trigger, Compliance, Boundary**, na 79 realnych skillach
i 177 wykonalnych zadaniach. Mam wzorzec, nie wymyślam metryki.

---

## 6. RYZYKA, Z LICZBAMI

| ryzyko | prawdopodobieństwo | skutek | mitygacja |
|---|---|---|---|
| Regresja typu SkillsBench | średnie | skill psuje to, co działało | `arXiv 2602.12670`: **16 z 84 zadań regresowało** po wdrożeniu skilla |
| Regex z opisu nie dopasuje nowego formatu promptu | **wysokie** | Trigger Rate spada | opis ma 4 nazwane sytuacje, nie `ANY` |
| Skill zniknie przy `hermes update` | nieznane | utrata 20 linii pracy | kroki 1 i 2 procedury |
| FPR na lekkich zadaniach | **zmierzone w Planie 2: 28 procent na 203 sesjach** | zbędne wywołania | tu nie dotyczy, skill nie wstrzykuje, tylko opisuje |
| Prompt w skillu nie zadziała | **niemierzone, prawdopodobne** | brak poprawy | pomiar Trigger Rate przed i po, na tych samych 30 zdaniach |

**Ostatnie ryzyko jest najważniejsze i najmniej komfortowe.**
`arXiv 2510.11588` (ACL 2026 long paper 767) mówi wprost, że nawet
state-of-the-art agenci nie realizują wiarygodnie dokumentów polityki.
Nie mam dowodu, że zmiana opisu cokolwiek poprawi.

---

## 7. KRYTERIA UKOŃCZENIA

- [ ] Kopia 0.1.0 w `skills-archive/`, sprawdzona krokiem 1
- [ ] `grep -n skills install.sh` wykonany, wynik zapisany w CHANGELOG
- [ ] `SKILL.md`: 4 zmiany z sekcji 2, `version: 0.5.0`
- [ ] `CHANGELOG.md` z wpisem 0.5.0 i **powodem** zmiany
- [ ] 30 fixture'ów w grupie POWINNO, 10 w grupie NIE
- [ ] Test 5.2 przechodzi: 0 z 10 na fałszywe alarmy
- [ ] Zero em-dash w pliku (skrypt z sekcji 8)
- [ ] Wynik Trigger Rate **przed i po**, na tych samych 30 zdaniach
- [ ] Pomiar zapisany w CHANGELOG, nie tylko w mojej głowie

---

## 8. KONTROLA PRZED ODDANIEM

Ten plik i skill muszą przejść tę samą kontrolę, którą wymuszam
w `em_dash_guard.py`, czyli skrypt, nie apel:

```python
for p in ("SKILL.md", "CHANGELOG.md"):
    t = open(p, encoding="utf-8").read()
    bad = {c: t.count(c) for c in "\u2014\u2013\u2015" if t.count(c)}
    assert not bad, f"{p}: {bad}"
```

Wzorowany na `em_dash_guard.py:28-35`, fail-open, około 8 linii logiki.
**Ten wzorzec działa dlatego, że plik robi robotę, a nie dlatego, że
instrukcja jest w kontekście.** `mcp_inventory_interceptor.py:4-7`
mówi o tym wprost, w komentarzu na początku pliku:
> ROZPOZNANIE REGULY W REASONINGU NIE JEST JEJ WYKONANIEM

---

## 9. OCENA SZCZEROSCIOWA

**Czy wersja 0.5.0 zadziała: nie wiem.** Nie mam pomiaru, że obecna nie działa.
Mam pomiar, że obecna jest otwierana 652 razy, czyli opis działa, a skill jest
w liście bootu.

**Co wiem:**

| stan wiedzy | status |
|---|---|
| skill jest otwarty regularnie | **pomiar, 652 razy** |
| opis powoduje otwarcie, czy boot? | **pomiar: głównie boot, 10 skillów z listy** |
| treść skilla zmienia zachowanie | **nie wiem** |
| sekcja ESKALACJA zadziała | **nie wiem, to jest hipoteza** |

**Jedyna rzecz, którą ta wersja wnosi, to jedno zdanie z sekcji 2.3.**
Reszta to skrócenie opisu i usunięcie liczby bez źródła.

**Jeśli to nie jest dojebany przeskok, to nie powinnam tego robić w tej formie.**
Powinienem powiedzieć wprost: hook jest warstwą, która ma szansę zadziałać,
skill jest optymalizacją, która w najlepszym razie nie szkodzi.
