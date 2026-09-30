# PLAN FINALNY 2: brama kolejnosci researchu

**Rodzaj:** plan wdrożenia. Zero zmian w produkcji wykonane.
**Powstał z:** 32 iteracje w `WORKSPACE/iteracje/PLAN2_iter_*.md`
**Data:** 2026-09-29
**Em-dash:** w pliku nie ma znaków U+2014, U+2013, U+2015

---

## 1. CO ZMIENILO SIE W TRAKCIE

Pierwszy plan napisałam, zanim sprawdziłam stan systemu. **Pięć elementów
w nim było nie do wdrożenia.** Pozostałe 27 iteracji je wykluczyło.

| element planu v0 | stan | dlaczego |
|---|---|---|
| wstrzyknięcie `{"context": ...}` na `pre_tool_call` | **niewykonalne** | `_RESPONSE_PARSERS` ma tam tylko `block`, `modify`, `approve` |
| detektor powtórzeń | **już istnieje** | `tool_guardrails.py`, 639 linii, `warnings_enabled: true` w config.yaml |
| 4 narzędzia w matcherze | **działa, ale kosztowniej niż myślałam** | `Compat*` to prezentuacja, 0 wystąpień w 308 852 wywołaniach |
| "zacznij od fazy miękkiej" | **nie istnieje w tej warstwie** | jedyna akcja to blokada |
| wykrywanie braku postępu mimo zmiennych danych | **nie zrobię regexem** | zmierzone FBR 28 procent |

---

## 2. POMIARY, KTÓRE UZASADNIAJĄ KAŻDY WYBÓR

### 2.1 Warstwa techniczna, zamknięta pomiarem

```
shell_hooks._RESPONSE_PARSERS = ['pre_tool_call', 'pre_verify']
transform_tool_result w kluczach:        False
plugins.VALID_HOOKS ma transform_tool_result:  True
```

Kompletny podpis `transform_tool_result`, 12 kwargsów, zmierzony przez
`unittest.mock.patch` na `hermes_cli.plugins.invoke_hook`, tak jak robi
`tests/tools/test_model_tools.py:38-40` w repo:
```
api_request_id, args, duration_ms, error_message, error_type, result,
session_id, status, task_id, tool_call_id, tool_name, turn_id
```
`tool_name` jest. `session_id` jest. `args` jest.
**`conversation_history` nie ma i nie będzie.**

Wzorzec do skopiowania jest już w repo,
`plugins/security-guidance/__init__.py:115`:
```python
def _on_transform_tool_result(tool_name="", args=None, result=None, **_):
    findings = [] if not isinstance(result, str) else _scan_args(tool_name, args)
    if not findings:
        return None
    return result + "\n\n" + _format_warning_block(findings)
```

`~/.hermes/plugins/` ma **zero** własnych pluginów z `transform_tool_result`.
Sprawdzone `ls`, nie zgadywane.

### 2.2 Warstwa zachowania, zamknięta pomiarem

`state.db`, 562 sesje interaktywne z 2026-09-25, metryka: ile probeów
przed pierwszym użyciem źródła.

| pierwsze wywołanie | n | źródło przed probe'em | ominięcie |
|---|---|---|---|
| `terminal`/`execute_code`/`write_file`/`patch` | 21 | **0** | **21 (100%)** |
| `kanban_*` | 32 | 29 (91%) | 3 (9%) |
| cokolwiek innego | 118 | 118 (100%) | 0 |

**Reguła jest skuteczna dokladnie wtedy, gdy pierwszy ruch jest źródłem.**
Jak pierwszy ruch jest probe'em, 0 procent w 21 na 21.
**Progowy charakter, nie probabilistyczny.**

### 2.3 FBR zmierzone, nie zgadywane

203 sesje z 1 do 4 wywołaniami, czyli zakres lekki:

```
warunek dawalby NOTICE:  57  (28.1%)
warunek by byl cichy:  146  (71.9%)
```

Rozkład 57:

```
41  persona/ROJ          email-agentka, siostra, wcielenie
10  benchmark            "write ONE complete, correct Python function"
 5  INNE                 "przejrzyj ten kod" (kod w promptcie), "wypisz pliki"
 1  odpowiedz jednym slowem
```

**Reguła oparta na `tool_name` nie odróżnia "braku źródła" od "zadania,
które nie wymaga źródła".** To jest fundamentalna pomylka kryterium.

### 2.4 Zależność, która unieważnia licznik po `tool_name`

```
wywolan execute_code/terminal z hyperspace_search lub web_search:  126
w unikalnych sesjach:  43
```
```python
from hermes_tools import web_search
queries = ['40+ różnych zapytań...']
```

Agent używa źródła **przez kod, nie przez narzędzie**. `tool_name` to
`execute_code`, czyli `PROBE`, czyli "jeszcze nie było źródła".
**Dziura jest obecna w realnych danych, 3 procent wolumenu.**

### 2.5 Dwie ślepe uliczki, zmierzone

Wariant A z regexu na `args` (`curl|wget|requests|http|pip install|git clone`):
**0 alarmów na 64 sesjach.** Nie odsiał fałszywych alarmów, odsiał wszystkie
trafienia. `himalaya list`, `python3 -c "def..."`, `find ~/.hermes` żadnego
z tych regexów nie mają.

Klasyfikacja `user_message` (persona, benchmark, konkretny temat):
```
persona / ROJ    46   (72%)
benchmark         10   (16%)
KONKRETNY TEMAT    8   (12%)
generyczne        0
pusty             0
```
A te 8 konkretnych tematów według liczby wywołań:
```
1-2 wywołania (lekkie)   5
3-5                      1
6-20                     0
>20 (ciężka)             2
```

**Nawet po poprawnej klasyfikacji, 5 z 8 konkretnych tematów to sesje
1-2 wywołaniowe.** Żeby wiedzieć, że pytanie jest lekkie, trzeba je zrozumieć.
Regex `user_message` tego nie zrobi.

---

## 3. DECYZJA ARCHITEKTURALNA

Trzy warianty, wszystkie z kosztem zmierzonym:

| wariant | FBR | koszt | przeżywa `hermes update` |
|---|---|---|---|
| W0 bez filtru | **28 procent, zmierzone** | zero | tak |
| próg 5 wywołań | niski, ale zabija ciężkie sesje zaczynające się od probe | zero | tak |
| **LLM-klasyfikator w `pre_llm_call`** | **niezmierzone, jedyny bez udokumentowanych fałszywych alarmów** | **jedno wywołanie na turę** | tak |

**Wybór: LLM-klasyfikator w `pre_llm_call`, zapis do pliku,
odczyt w `transform_tool_result`.**

Powody, w kolejności wagi:

1. **FBR 28 procent to gorsze niż brak bramki.** `arXiv 2603.18059` podaje
   False Block Rate jako metrykę obok Violation Prevention Rate. Bramka,
   której fałszywe alarmy uczą agenta ignorować system, jest gorsza od braku.
2. **`pre_llm_call` widzi `user_message`, `transform_tool_result` nie.**
   To jest jedyna asymetria, która daje informację o tym, czego agent szuka.
3. **`~/.hermes/plugins/` przeżywa `hermes update`, `~/.hermes/hermes-agent/` nie.**
   `install.sh` robi `git reset --hard origin/$BRANCH`, więc
   `tool_guardrails.py` zniknie. Plugin w `~/.hermes/plugins/` zostaje.
   To przechyliło wybór z jądra na plugin.
4. **Odwracalność: `rm -rf` katalogu.** Nie dotyka `config.yaml`, nie wymaga
   allowlistu, nie wymaga `hermes hooks doctor`.

Koszt: 1,5 sekundy na `nemotron-3.5-lightning` na turę, czyli 2,5 procent
budżetu sesji przy 60 sekundach na turę.

---

## 4. ARCHITEKTURA

```
~/.hermes/plugins/research-order/
  plugin.yaml
  __init__.py
  tests/test_gate.py

  pre_llm_call           -> KLASYFIKACJA: czy user_message ma konkretny temat,
                             ktorego nie ma na dysku. Zapis do pliku stanu.
  transform_tool_result  -> DOPISEK do wyniku, jesli w sesji nie bylo jeszcze
                             zrodla, a session_state mowi ze temat wymaga zrodla.
```

### 4.1 Stan: plik, nie pamiec

Plugin Pythona ma dostep do pamieci procesu, ale `pre_llm_call` i
`transform_tool_result` moga byc w **roznych procesach** przy gateway
i przy workstacji. Plik z `fcntl.flock` z timeoutem 1 sekundy,
`os.replace` dla atomowosci, TTL 1800 sekund, klucz `session_id`.

Wzorzec z `project-admission-guard.py:32-39`, `log()` na JSONL z kluczem
`ts` w UTC, `mkdir(parents=True, exist_ok=True)` przy pierwszym zapisie.

### 4.2 Dwa hooki, dwa allowlisty, zero shell hookow

Nie `hooks:` w `config.yaml`. To jest plugin, rejestrowany przez
`plugin.yaml` i `register(ctx)`. Wzorzec z
`plugins/security-guidance/__init__.py:131-133`.

### 4.3 Zabezpieczenie przed obejściem przez kod

126 wywolań z iteracji 31. Regex na `args` w `pre_tool_call`:
```python
SRC_IN_CODE = re.compile(
    r"hyperspace_search|hyperspace_store|web_search|web_extract|"
    r"requests\.|urllib|curl |wget |httpx", re.I)
```
Ustawia `src = True`. Nie liczy się jako źródło dla agenta, bo agent wie,
że źródło jest, ale mechanizm to zapisuje.

### 4.4 Co plugin NIE robi

- **Nie blokuje.** `transform_tool_result` zwraca dopisek, `pre_tool_call`
  zwraca `None`. RA = 1.0 z definicji, bo żadne wywołanie nie jest odrzucane.
- **Nie liczy `read_file` ani `search_files` jako źródła sieciowego.**
  Pomiar z iteracji 22: krok 2 na dysku działa w 84 procentach,
  sieć w 86 procentach. Obie są źródłem, ale to, co zmienia decyzję agenta,
  to sieć. Używam obu.
- **Nie dopisuje NOTICE do wyników błędów.** Wzorzec z
  `security-guidance/__init__.py:121-127`, `status == "error"` zwraca `None`.
- **Nie liczy `read_file` w liczniku probe'ów**, bo inwentaryzacja jest dozwolona.

---

## 5. NOTICE

Treść musi być faktem, nie instrukcją. `arXiv 2606.25189` (ActPlane) mierzy,
że semantic feedback konwertuje wykrycia na zgodność na **97,7 procent**,
a ten sam silnik bez feedbacku daje 27 wyników zamiast 86. Wstrzyknięcie faktu
działa, bo zmienia to, co agent widzi.

```
[hermes note: pierwsze wywolanie diagnostyczne w tej sesji, a zrodla nie bylo.
Na tym komputerze przeanalizowano 562 sesje: w 86 procentach zrodlo bylo
pierwszym wywolaniem, a w sesjach zaczynajacych sie od pliku terminal albo
skryptu, zrodla nie bylo w 21 na 21. Zanim napiszesz kolejny skrypt
diagnostyczny: hyperspace_search, albo ~/.hermes/config.yaml, albo
~/.hermes/state.db, gdzie jest 308 852 wywolan z 15 953 sesji i 284
otwartych skillow. Pamiec HSDB ma 73 wpisy, wiec slowo "mam to" nie wystarcza,
sprawdz co tam jest.]
```

Ostatnie zdanie jest z mojego pomiaru HSDB z 2026-09-28: kolekcja
`gniewka_omniscient` ma 73 wpisy, a skill `gniewka-boot-and-memory`
deklaruje 407 tysięcy. **Różnica trzech do czterech rzędów wielkości** to
aktywne ryzyko, nie brak danych.

---

## 6. METRYKI, Z DEFINICJAMI

Z `arXiv 2603.18059`, sekcja A-E, plus miara z Planu 2 iteracji 24.

| metryka | definicja | prog | skąd |
|---|---|---|---|
| **VPR** | wyzwolenia, po których agent faktycznie sprawdził źródło / wszystkie wyzwolenia | > 0 i mierzone | VPR z paperu |
| **FBR** | wyzwolenia bez zmiany zachowania / wszystkie wyzwolenia | < 10 procent | FBR z paperu |
| **RA** | wykonane wywołania / minimalnie wymagane | **= 1.0** | RA z paperu |
| **TP** | sesje, w których klasyfikator poprawnie uznał że źródła trzeba | raportowane, bez progu | własne |
| **TN** | sesje, w których klasyfikator poprawnie uznał że nie trzeba | raportowane, bez progu | własne |

**FPR z Planu 2, iteracja 29, wynosi 28 procent na 203 lekkich sesjach.**
To jest linia odniesienia dla klasyfikatora LLM. Jeśli klasyfikator da
więcej niż 28 procent FBR, **nie wdrażamy**, bo wtedy jest gorszy od W0.

---

## 7. PROCEDURA

| krok | co | czas | odwracalne |
|---|---|---|---|
| 0 | pomiar kwargs w pluginie: `print(kwargs.keys())`, jedno wywołanie, wycofanie | 30 s | tak |
| 1 | `cp -a ~/.hermes/hermes-agent /tmp` przed jakąkolwiek zmianą w `hermes-agent` | 3 min | tak |
| 2 | `handler.py` bez rejestracji, z testami na 22 fixture'ach z Planu 1 | 1 h | tak |
| 3 | testy jednostkowe, z pomiarem przez `${PIPESTATUS[0]}` nie `$?` po pipe | 30 min | tak |
| 4 | pomiar klasyfikatora na 374 sesjach z `state.db` przed wdrożeniem | 1 h | tak, odczyt |
| 5 | rejestracja w `~/.hermes/plugins/`, jeden katalog, zero zmian w config | 5 min | `rm -rf` |
| 6 | pomiar na 20 sesjach, log własny, nie `state.db` | 2 tyg. | `rm -rf` |
| 7 | decyzja na danych: FBR, VPR, RA | 1 h | - |

Krok 0 jest formalny, bo iteracja 13 napisała „nie wiem" o `**kwargs`,
a iteracja 26 to rozstrzygnęła pomiarem. **Powtórzenie na żywo przy
rejestracji, bo to inny proces.**

Krok 4 jest najważniejszy i najdroższy. **Jeśli klasyfikator da FBR wyższy
niż 28 procent, plan się zatrzymuje przed wdrożeniem.**

---

## 8. TESTY, KTÓRE LAPIĄ TO, CO PRZEPISZ

Iteracja 28: napisałam kod z martwą linią, dodałam przypis, że linia jest
martwa, i zostawiłam ją. **Przypis nie jest kontrolą, jest komunikatem.**

```python
def test_zrodlo_przed_probe_nie_daje_notice():
    _on_pre_llm_call(user_message="sprawdz moj config", session_id="s1")
    _on_pre_tool_call(tool_name="read_file", session_id="s1")
    r = _on_transform_tool_result(tool_name="terminal", result="out", session_id="s1")
    assert r is None, "zrodlo przed probe nie moze dac NOTICE"

def test_probe_jako_pierwsze_daje_notice():
    _on_pre_llm_call(user_message="sprawdz czemu kimi k3 nie dziala", session_id="s2")
    r = _on_transform_tool_result(tool_name="terminal", result="out", session_id="s2")
    assert "hermes note" in r, "probe jako pierwsze wywolanie musi dac NOTICE"

def test_benchmark_nie_daje_notice():
    _on_pre_llm_call(user_message="You are solving a benchmark task. "
                      "Write ONE complete, correct Python function", session_id="s3")
    r = _on_transform_tool_result(tool_name="write_file", result="{}", session_id="s3")
    assert r is None, "benchmark nie wymaga zrodla"

def test_persona_nie_daje_notice():
    _on_pre_llm_call(user_message="Jestes email-agentka, pytas siostre", session_id="s4")
    r = _on_transform_tool_result(tool_name="terminal", result="", session_id="s4")
    assert r is None, "persona nie wymaga zrodla"

def test_zrodlo_przez_kod_liczy_sie():
    _on_pre_tool_call(tool_name="execute_code",
                      args={"code": "from hermes_tools import web_search"}, session_id="s5")
    r = _on_transform_tool_result(tool_name="terminal", result="out", session_id="s5")
    assert r is None, "zrodlo przez kod to zrodlo, 126 wywolan to potwierdza"

def test_bledowy_wynik_nie_dostaje_notice():
    r = _on_transform_tool_result(tool_name="terminal", result='{"error":"x"}',
                                  status="error", session_id="s6")
    assert r is None, "wzorzec security-guidance linia 121-127"

def test_brak_session_id_nie_pisze_do_pliku():
    r = _on_transform_tool_result(tool_name="terminal", result="out", session_id="")
    assert r is None, "pusty session_id oznacza brak stanu"
```

**Siedem testów, sześć kierunków.** Test 5 istnieje, bo iteracja 31 znalazła
126 wywołań z `hermes_tools`. Testy 3 i 4 istnieją, bo iteracja 29 znalazła
28 procent FBR, z czego 41 to persona i 10 to benchmark.

---

## 9. RYZYKA

| ryzyko | prawdopodobieństwo | skutek | mitygacja |
|---|---|---|---|
| FBR klasyfikatora wyższy niż 28 procent | **średnie** | brama gorsza od W0, krok 4 to zatrzymuje | pomiar przed wdrożeniem |
| Regex na prompt ułamie się przy nowym formacie | **wysokie** | ciche milczenie klasyfikatora | pomiar TP i TN raportowany, bez progu |
| `pre_llm_call` i `transform_tool_result` w różnych procesach | **średnie** | brak stanu, NOTICE nie działa | plik z flock, nie pamięć |
| Czas na klasyfikator: 1,5 s na turę | niskie | 2,5 procent budżetu sesji | pomiar w kroku 6 |
| `hermes update` skasuje `hermes-agent`, nie `plugins/` | **pewne, korzystne** | plugin przeżywa | krok 1 jako zabezpieczenie |
| NOTICE nie zmienia zachowania | **niezmierzone** | bramka bez efektu | to jest cała wartość projektu, nie da się tego zmierzyć inaczej niż wdrożeniem |

**Ostatnie ryzyko jest sednem.** Cała wartość projektu to hipoteza, że
dopisek w miejscu decyzji zmieni zachowanie. `arXiv 2606.25189` mierzy 97,7
procent konwersji wykryć na zgodność dla decyzji semantycznych w jądrze.
**Ja nie mam takiego pomiaru dla swojego NOTICE.** Wiem, że mechanizm jest
analogiczny. Nie wiem, że zadziała na moim tekście.

---

## 10. KRYTERIA UKOŃCZENIA

- [ ] Kopia `hermes-agent` przed zmianami, krok 1
- [ ] Klasyfikator zmierzony na 374 sesjach **przed** wdrożeniem
- [ ] FBR klasyfikatora poniżej 28 procent, inaczej stop
- [ ] 7 testów jednostkowych, pomiar przez `${PIPESTATUS[0]}`
- [ ] Plugin zarejestrowany w `~/.hermes/plugins/`, zero zmian w `config.yaml`
- [ ] `hermes --version` zapisany w CHANGELOG, `0.21.5+4188.g925b25d` w chwili pisania
- [ ] 20 sesji pomiaru z własnym logiem, nie z `state.db`
- [ ] FBR, VPR, RA raportowane, RA musi być 1.0
- [ ] Zero em-dash w pliku, sprawdzone skryptem

---

## 11. OCENA SZCZEROSCIOWA

**Czy ta bramka zadziała: nie wiem.** Nie mam pomiaru, że NOTICE
w miejscu decyzji zmienia zachowanie modelu w tej konfiguracji.
`arXiv 2606.25189` mierzy coś podobnego w jądrze, 97,7 procent, ale to inny
tekst i inna warstwa.

**Co wiem, wszystko z pomiaru:**

| stan wiedzy | podstawa |
|---|---|
| shell hooki nie widzą `transform_tool_result` | pomiar kodu |
| plugin widzi `tool_name`, `session_id`, `args` | pomiar na żywo |
| reguła działa w 86 procentach, gdy źródło pierwsze | pomiar 562 sesji |
| reguła nie działa w 100 procentach, gdy probe pierwszy | pomiar 21 sesji |
| W0 ma FBR 28 procent na lekkich zadaniach | pomiar 203 sesji |
| 126 wywołań używa źródła przez kod | pomiar kodu i sesji |
| skill jest otwarty 652 razy | pomiar 11 529 wywołań |

**Trzy warianty, jeden wybór, i wybór nie jest oczywisty.**
Bramka z deterministycznym FBR 28 procent jest najprostsza i najtańsza.
Bramka z LLM-klasyfikatorem jest droższa i jej FBR jest niezmierzone.

**Wybrałem droższą, bo `arXiv 2603.18059` mazywa FBR metryką obok VPR, a bramka
ucząca agenta ignorować system jest gorsza od braku.** Ale to jest mój wybór
z wiedzą o koszcie, nie z pomiarem, że wygra.

**Jeśli klasyfikator da FBR powyżej 28 procent w kroku 4, plan się zatrzymuje
i wracamy do decyzji, która jest w Planie 1, czyli do jednego zdania
w sekcji ESKALACJA.**
