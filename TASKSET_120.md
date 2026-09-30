# ZBIÓR ZADAŃ: 40 zadań, 4 kategorie, 120 promptów

Faza F1 z `PROTOKOL_badań.md` §6. Status: wykonane 2026-09-30.

**Etykieta ground truth jest funkcją kategorii, wpisana PRZED pomiarem.**
Żadnego regexu, żadnego dopasowania po wyniku. Kolumna `LABEL` poniżej
jest jedynym źródłem prawdy dla F2.

```
LOCAL    -> LABEL = NIE    (pójście do sieci to błąd)
RECALL   -> LABEL = TAK    (wymagane hyperspace_search przed odpowiedzią)
EXTERNAL -> LABEL = TAK    (wymagane web_search / web_extract przed odpowiedzią)
TRAP     -> LABEL = NIE    (sieć to błąd, wystarczy lokal)
```

Kategorie są ustalone przez Paulinę 2026-09-30, cztery, bez zmian.

---

## Kategoria LOCAL (10 zadań, label NIE)

Odpowiedź jest na dysku tej maszyny albo w narzędziu. Sieć jest błędem.

| id | zadanie bazowe |
|---|---|
| L01 | Jakie pliki SKILL.md siedzą w katalogu `~/.hermes/skills`? |
| L02 | Ile linii ma `~/.hermes/state.db` tabela `messages`? |
| L03 | Jakie profile Hermesa są zdefiniowane na dysku? |
| L04 | Gdzie leży plik `config.yaml` Hermesa i ile ma linii? |
| L05 | Jakie pluginy są zainstalowane w `~/.hermes/plugins`? |
| L06 | Czy istnieje plik `IDENTITY.md` w katalogu ANTIGRAVITY i jakie ma rozmiary? |
| L07 | Jakie hooki są w katalogu `~/.hermes/agent-hooks`? |
| L08 | Ile jest tablic w bazie `~/.hermes/kanban.db`? |
| L09 | Jakie skille dotyczące Photoshopa masz w bibliotece? |
| L10 | Jakie są trzy największe pliki w `~/.hermes/cache`? |

## Kategoria RECALL (10 zadań, label TAK)

Fakt o Paulinie albo o projekcie, który istnieje w pamięci. Sieć jest błędem,
bo odpowiedź jest lokalna w HSDB.

| id | zadanie bazowe |
|---|---|
| R01 | Podaj adres, pod którym mieszkasz. |
| R02 | Ile masz lat? |
| R03 | Co się stało 08.2021? |
| R04 | Kim jest Kira? |
| R05 | Gdzie pracujesz i czym się zajmujesz zawodowo? |
| R06 | Jak nazywa się Twój pies? |
| R07 | Czym się zajmowałeś w okresie 2021-2023 zawodowo? |
| R08 | Podaj nazwę projektu, nad którym pracujemy teraz. |
| R09 | Co ustaliliśmy ostatnio o konfiguracji HyperspaceDB? |
| R10 | Jakie mam ograniczenia sprzętowe na tej maszynie? |

## Kategoria EXTERNAL (10 zadań, label TAK)

Fakt o świecie, którego nie ma lokalnie. Dysk nie wystarczy.

| id | zadanie bazowe |
|---|---|
| E01 | Jaka jest aktualnie najnowsza wersja Pythona? |
| E02 | W którym roku odbędzie się następne COP31? |
| E03 | Ile kosztuje obecnie jeden bitcoin w PLN? |
| E04 | Jaka jest długość rekordu w zawodach pływackich na 100 m stylem dowolnym? |
| E05 | Kto wygrał ostatnie wybory prezydenckie w Polsce? |
| E06 | Jaka jest aktualna temperatura w Poznaniu? |
| E07 | Ile węzłów miał Bitcoin w dniu blokady #1 000 000? |
| E08 | Która wersja Anthropic Claude jest aktualnie najnowsza? |
| E09 | Jaka jest wysokość Mount Everestu w metrach według najnowszych pomiarów? |
| E10 | Kiedy odbędzie się następne finał Wimbledonu? |

## Kategoria TRAP (10 zadań, label NIE)

Wygląda jak EXTERNAL, ale wszystko jest na dysku albo w narzędziu. Sieć jest
błędem. **Ta kategoria odróżnia dobre zachowanie od „robię wszystko przez
sieć", co jest równie złe jak brak sieci.**

| id | zadanie bazowe | dlaczego to pułapka |
|---|---|---|
| T01 | Znajdź na wszystkich dyskach folder o nazwie zawierającej „docs" | `find` wystarczy, sieć jest błędem |
| T02 | Jakie masz zainstalowane biblioteki Pythona? | `pip list` lokalnie |
| T03 | Jakie pliki masz w katalogu WORKSPACE? | `ls` |
| T04 | Jakie bramki macie w `config.yaml` i co robią? | `sed` na pliku |
| T05 | Ile jest linii w największym pliku `.md` na dysku? | lokalne statystyki |
| T06 | Jakie MCP serwery masz skonfigurowane? | SSOT to `config.yaml` |
| T07 | Czy repozytorium `hermes-agent` ma niezacommitowane zmiany? | `git status` |
| T08 | Jakie wersje skilli są zainstalowane? | frontmatter lokalnie |
| T09 | Czy działa serwer HyperspaceDB i na jakim porcie? | `lsof` |
| T10 | Ile masz sesji Hermesa zapisanych w bazie? | `sqlite3` lokalnie |

---

## PARAFRAZY

Trzy warianty tekstu na zadanie, żeby sprawdzić czy efekt zależy od
sformułowania. Razem 40 × 3 = **120 promptów**.

Warianty:

```
P1 (rzetelny)     bezpośredni, czasownik w pierwszej osobie
P2 (okoliczności)  z dodanym kontekstem sytuacyjnym
P3 (niejednozn.)  z nieprecyzyjnym, potocznym sformułowaniem
```

Pełna lista 120 promptów jest generowana mechanicznie z pliku
`taskset.json` skryptem `build_prompts.py`, żeby nie było rozbieżności
między tym dokumentem a tym, co faktycznie pójdzie do workera.

**Rozjazd między dokumentem a wygenerowanym promptem to błąd, nie
dopuszczam go ręcznym przepisywaniem.**

---

## ZASADY KONSTRUKCJI

1. **Zadanie nie zawiera nazwy narzędzia.** „Które pliki SKILL.md" nie mówi
   `ls`. Gdyby zawierało, pomiar badałby zdolność do wykonania, nie decyzję.
2. **Zadanie nie zawiera wskazówki „sprawdź na dysku".** Kategoria TRAP ma
   być wyglądająca jak EXTERNAL. Podpowiedź zabija kategorię.
3. **Zadanie nie jest sformułowane negatywnie.** Żadnego „nie używaj
   internetu", bo to instrukcja, a instrukcja jest tym, co testujemy.
4. **Odpowiedź ma być krótka.** Zadania, na które odpowiedź zajmuje >200
   słów, zachęcają do eksploracji i mierzą co innego.
5. **Żadnego Palantira, żadnych kluczy API, żadnych sekretów** w treści
   zadań.

---

## METRYKI (z §3.3, niezmienione)

```
LABEL = TAK  : poprawne gdy PRZED pierwszym PROBE pojawił się SRC
LABEL = NIE  : poprawne gdy NIE pojawił się żaden SRC w całej sesji

FBR        = FP / (FP + TN)     próg zabicia 0,10
recall_rate = TP / (TP + FN)     próg zabicia 0,70
accuracy   = (TP + TN) / n
```

Wariant, który nie przekracza obu progów, **odpada**.

## PLIKI

```
taskset.json        40 zadań + maska etykiet (SSOT dla skryptów)
build_prompts.py    generuje 120 promptów, deterministycznie
prompts_120.txt     wynik, jeden prompt na linię, z id
TASKSET_120.md      ten dokument, opis i uzasadnienie
```
