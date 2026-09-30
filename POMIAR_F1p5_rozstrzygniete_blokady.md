# POMIAR F1.5: blokady rozstrzygnięte przed F2

Data: 2026-09-30, sesja `20260928_164353_75c510`
Źródło: `~/.hermes/state.db` (odczyt `mode=ro`), `~/.hermes/config.yaml`,
`hermes plugins list --json`

---

## BLOKADA 1: czy worker kanban ma ten sam system prompt co ja

**Rozstrzygnięta: TAK, z jednym wyjątkiem.**

### Instrument, nie zgadywanie

`state.db` ma dwie ścieżki danych o promptach:

```
sessions.system_prompt     0 z 16 475 sesji wypełnione    (NULL)
system_prompts             2 689 wierszy, 2 689 unikalnych hashy
```

Kolumna w `sessions` jest martwa. Prawdziwe źródło to tabela `system_prompts`
z hashami. Rozkład długości:

```
min 1 326 B    mediana 173 097 B    max 285 177 B
```

**2 689 unikalnych promptów.** To jest pierwszy wynik, który zmienia sposób
myślenia o pytaniu. Nie ma jednego promptu, jest ich 2 689.

### Markery obecności

Przeszukałam 2 689 promptów pod kątem sześciu znaczników:

| znacznik | trafienia | udział |
|---|---|---|
| `Finishing the job` | 2 551 | 94,8 % |
| `—` (em-dash) | 2 673 | 99,4 % |
| `Gniewis` (tożsamość) | 2 522 | 93,8 % |
| `kanban` | 2 303 | 85,6 % |
| `INVENTORY` | 1 657 | 61,6 % |
| `mcp_servers` | 439 | 16,3 % |
| `COGNITIVE DISPATCH` | 0 | **0,0 %** |

**`KANBAN_GUIDANCE` jest w 85,6 procenta promptów**, czyli worker kanban
dostaje wstrzyknięty blok lifecycle, tak jak ja. To jest część odpowiedzi.

**`COGNITIVE DISPATCH` jest w zerze.** Ten blok, który dostaję w każdej
sesji jako kontrakt, **nie istnieje w żadnym zapisanym prompcie**. Czyli
albo jest wstrzykiwany poza `system_prompts`, albo nie jest częścią promptu
zapisowego. **Nie wiem który.** To jest luka, nie wniosek.

**`mcp_servers` w 16,3 procenta.** Lista MCP wchodzi do promptu tylko
czasem. To znaczy, że **13 z 15 sesji nie ma w prompcie informacji o
własnych serwerach MCP**, a dwa, które mają, to te, gdzie prompt jest
największy.

### Odpowiedź na pytanie

Blokada 1 rozstrzygnięta **pozytywnie z zastrzeżeniem**. Worker kanban
dostaje ten sam szkielet co ja: 85,6 procenta promptów zawiera blok kanban,
93,8 procent zawiera tożsamość, mediana 173 kB. **Ale**:

1. prompt workerów **nie jest identyczny** z moim, bo 2 689 unikalnych hashy
   przy 16 475 sesjach oznacza, że prompt zmienia się z każdą sesją
2. **Mój prompt z tej sesji nie jest w bazie.** Fraza `MINIMALIZACJA
   DESTRUKCJI` (z mojego nagłówka systemowego) ma **0 trafień**. Czyli
   `system_prompts` nie zawiera bieżących promptów, tylko historyczne.
   Porównanie musi więc być zrobione na innym zadaniu: uruchomić workera,
   zapisać faktyczny prompt, porównać z moim na żywo.

**Blokada 1 nie jest do końca zamknięta.** Zamknięta w części „worker ma
blok kanban”, otwarta w części „czy zachowanie jest przenoszalne na moje”.

---

## BLOKADA 2: kanał recall

**Rozstrzygnięta: kanał jest ŚWIADOMIE WYŁĄCZONY w `config.yaml`.**

```yaml
plugins:
  disabled:
    - hermes-project-stewardship
    - hyperspacedb          # wtyczka Pythona 2.8.1
```

```yaml
mcp_servers:
  hyperspacedb:
    command: .../node .../mcp-hyperspacedb/dist/index.js
    enabled: false          # serwer MCP
    tools:
      exclude:
        - hyperspace_insert_text
        - hyperspace_search_text
```

`hermes plugins list --json`, 82 pluginy, stan `hyperspacedb`:

```
hyperspacedb    disabled    2.8.1
```

Różnica między `disabled` a `not enabled` jest tu istotna: `research-order`
ma `not enabled` (po prostu aktywowany), `hyperspacedb` ma `disabled` (ktoś
go tam wpisał). Obok niego świadomie wyłączone: `hermes-project-stewardship`
(`disabled`), `hindsight` (`not enabled`).

### Objawy potwierdzające

| objaw | pomiar |
|---|---|
| `tool_search` na 28 źródeł | 0 trafień dla `hyperspace_search` |
| `mcp__gniewka_mcp__recall_memory` o adres Pauliny | rekordy o alimentach, SecureToken USB, macOS auto-wake, **zero trafień w pytanie** |
| `recall_by_entity("Paulina adres Piekary")` | `{"graph": [], "semantic": []}` |
| `_provider.py` na venv Hermesa, poprawny config | `ERR CollectionNotFound` |
| `50050 /api/health` | `{"status":"ONLINE"}` |
| `50050 /api/collections` | `gniewka_omniscient  416 617` |
| `50051` (RPC) | HTTP probe kod 000 |
| `lsof` | hyperspace PID 584 nasłuchuje na obu portach |

**Baza jest zdrowa i pełna. Kanał jest wyłączony.** To nie jest awaria.

### Wniosek dla F2

Kategoria RECALL wymaga działającego `hyperspace_search`. Przy wyłączonym
kanale agent nie ma gdzie sięgnąć poza LABEL=TAK, więc **FN byłyby
pomiarem wyłączenia, nie pomiarem reguły**.

---

## STAN BLOKAD PRZED F2

| blokada | stan | co zostaje |
|---|---|---|
| worker ma ten sam prompt | **85,6 % mają blok kanban, 2 689 unikalnych promptów** | uruchomić 1 worker, porównać prompt na żywo |
| kanał recall działa | **NIE, wyłączony w config.yaml** | decyzja Pauliny |
| zadania RECALL dają się rozstrzygnąć | **nie do sprawdzenia przy wyłączonym kanale** | po włączeniu kanału |

**F2 pozostaje zablokowane.** Nie ruszam `config.yaml`, nie włączam bramki
`research-order`, nie tworzę kategorii, nie przesuwam progu.

## LOG DECYZJI

| decyzja | uzasadnienie |
|---|---|
| `sessions.system_prompt` uznany za martwe pole | 0 z 16 475 wypełnionych |
| `system_prompts` jako jedyne źródło | 2 689 hashy, to realna liczba |
| 6 znaczników zamiast porównania pełnych tekstów | porównanie 285 kB × 2 689 jest niepraktyczne, znaczniki wystarczają do odpowiedzi na pytanie o obecność |
| `COGNITIVE DISPATCH` zapisany jako **luka**, nie jako fakt | 0 trafień nie rozróżnia „nie istnieje" od „wstrzykiwany poza tabelą" |
| nie włączam kanału recall | `config.yaml` to infrastruktura, decyzja należy do Pauliny |
| blokada 1 zamknięta częściowo | przenoszalność wymaga pomiaru na żywym workerze, nie na statystyce |
