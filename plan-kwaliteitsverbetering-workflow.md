# Plan kwaliteitsverbetering blogpost-workflow

*Opgesteld: 2026-08-02. Bron: code-analyse van `scripts/orchestrator/`, `server.py`, `web/`
en `.claude/agents/` op commit `cec8f5e`.*

Dit document is het startpunt voor de uitvoering. Het bevat eerst de bevindingen met hun
vindplaats en de meting die eronder ligt, daarna het plan in vijf blokken.

## Uitvoeringsstatus

| blok | status |
|---|---|
| Blok 0 — stabiliseren | **af** (2026-08-14) |
| Blok A — RAG bruikbaar maken | **af** (2026-08-14) |
| B1 — alignment-gate | **af** (2026-08-14), via een andere route dan hieronder staat |
| Blok D — veilig centraal | open, volgende stap |
| Blok C — execution plane | open |
| B2 — socratische chat | open |

Gemeten na blok 0 + A: 70 tests groen (51 bestaand, 19 nieuw in `tests/test_rag_archive.py`);
index 2915 chunks uit 13 lokale slugs en 57 WP-slugs; `draft.md` levert 547 chunks;
`reference/corpus-inventaris.md` dekt alle 61 posts.

Eén bevinding is bijgesteld tijdens de uitvoering. De oorzaak van 1.3a was niet de
ontbrekende lock, maar het indexpad: `LocalRAGArchive` legde dat vast bij import, terwijl
`tests/test_server_api.py` `BLOGPOST_POSTS_DIR` naar een tijdelijke map verzet. Elke
testrun schreef daardoor een index over een lege postmap over de echte index heen — exact
het waargenomen patroon van 1633 WordPress-chunks plus tien `briefing.md`-chunks. Het
indexpad volgt nu de actuele postmap; `tests/test_rag_archive.py::TestPostmapWisseling`
legt dat vast. De lock is er ook.

**Modeladvies voor de uitvoering: Opus.** De codebase heeft een aantoonbaar patroon van
implementaties die correct ogen maar het niet zijn (zie B1 en B2). De fouten in blok A zijn
stil: de index oogt gevuld terwijl hij het verkeerde bevat, en dat merk je pas drie
blogposts later. Sonnet is verdedigbaar voor blok 0 en blok D.

---

## 1. Bevindingen

### 1.1 Er is geen executie-laag

In de hele Python-codebase staat **geen enkele LLM-aanroep**. Geen `anthropic`, geen Agent
SDK, geen subprocess naar `claude`. De enige subprocess-aanroepen zijn `pdftotext`
(`haal_bron.py:54`) en de SVG-renderer (`render_svg.py:93`).

`WorkflowService.run_phase` (`scripts/orchestrator/service.py:139`) zet de status op
`running`, logt, en geeft een `agent_brief` terug: een stuk **tekst**. Het retourveld zegt
het zelf: `"Voer de agent/script uit; daarna: complete {phase}"`.

De uitvoerder is dus Claude Code op de laptop, aangestuurd door de skill. De web-UI is een
afstandsbediening voor een state machine die zelf niets uitvoert. Met de laptop uit kun je
fases starten en goedkeuren, maar er wordt geen letter geschreven.

Dit blokkeert het doel "centraal doordraaien" volledig. Geen enkele ADR dekt deze keuze.

### 1.2 De RAG is gebouwd maar op niemand aangesloten

Zoekopdracht op `rag_cli`, `search_archive` en `archive_vectorstore` door `.claude/` geeft
één treffer, in `.claude/agents/blogpost-onderzoeker.md:19`, in de toekomende tijd:

> "Later wordt dit één query op een RAG-index over de bestaande posts."

`briefs.py` noemt de RAG nergens. Geen enkele agent-brief instrueert een subagent om te
zoeken. De onderzoeker haalt nog steeds zelf de twintig nieuwste posts op via de WP REST API.

Gevolg, gemeten: van de 61 posts op edwinvandillen.nl worden er **15** aangehaald in de
intentie-reeks, waarvan tien de reeks zelf zijn. Posts 205 t/m 274 vallen structureel buiten
het venster van twintig en zijn daardoor onzichtbaar. Daar zit juist het intentie-materiaal:

| id | datum | titel |
|---|---|---|
| 205 | 2026-01-11 | De Vier Dimensies van AI-Integratie in Software Engineering |
| 211 | 2026-02-08 | De transitie naar de Strategische Orchestrator: Intentie-Ecosysteem Model |
| 219 | 2026-02-16 | De synergie tussen intentie en volwassenheid: sturen op output versus outcome |
| 224 | 2026-02-22 | De Context-Match: waarom je teamfluency moet passen bij je probleemruimte |
| 251 | 2026-03-10 | Het vergroten van de outcome van Software Engineering |
| 353 | 2026-04-16 | AI-systemen worden deterministischer |
| 449 | 2026-07-07 | De Context Space vastleggen (concept) |
| 189 | 2021-05-23 | The machine that makes the machine (concept) |

Idem het begrip **stroomopwaarts**: dat komt op de site precies één keer voor, in `?p=398`
onder "Dimensie 2: stroomopwaarts vs. stroomafwaarts", en is de eigen positionering
tegenover Böckeler. In de hele repo komt het woord niet voor.

### 1.3 Vijf defecten in de RAG zelf

Alles in `scripts/orchestrator/rag_archive.py`.

**a. De index bevat geen enkel lokaal artefact.** Gemeten op de opgeslagen index (3,7 MB,
1643 chunks): filenames zijn uitsluitend `{'wordpress_live', 'briefing.md'}`. De enige
lokale slug is `socratische-ai-architectuur`, een post-map die niet meer bestaat. Een verse
volledige index over hetzelfde materiaal levert **1282 lokale chunks** uit 13 slugs op
(547 `draft.md`, 396 `outline.md`, 339 `synthese.md`). Al het werk in uitvoering ontbreekt
dus in de index die de consistentiecheck moet voeden.

**b. Incrementeel indexeren slaat gewijzigde posts permanent over.** `index_all_posts` bouwt
`indexed_slugs` uit bestaande documenten en doet `continue` zodra een slug bekend is. Een
herschreven draft wordt nooit opnieuw geïndexeerd. Voor WordPress geldt hetzelfde via de
`chunk_id`-dedupe: een gewijzigde alinea komt er als nieuwe chunk bij, de oude blijft staan.
De index loopt monotoon vol met verouderde tekst.

**c. Verwijderde posts blijven eeuwig in de index.** Geen tombstoning; vandaar de spookslug
onder a.

**d. Het is geen TF-IDF en geen vectorstore.** ADR-006 belooft "een lokale vector-database
met embeddings" en `server.py` noemt het endpoint "Zoek semantisch". De implementatie is
cosine over ruwe token-counts, **zonder enige IDF-weging**. Zonder IDF domineren
stopwoorden en algemene vaktermen. Retrieval werkt daardoor redelijk op letterlijke termen
(`"stroomopwaarts harnessing"` vindt de juiste passage in `?p=398`), maar faalt op precies
het geval waarvoor de RAG bedoeld is: "waar heb ik dit idee eerder in andere woorden gezegd".

**e. Gedeelde mutable singleton zonder lock.** `archive_vectorstore` is een module-level
instantie. De achtergrond-indexer uit `/api/rag/reindex-async` en
`validate_archival_alignment` (`archival_validator.py:24`, die bij **elke** aanroep een
volledige herindexering doet, synchroon, inclusief WP-fetch met `time.sleep(0.4)` per
pagina, binnen een HTTP-request) muteren dezelfde `self.documents` en schrijven allebei
`save_index()`. Laatste schrijver wint en kan de ander wissen. Dit is de waarschijnlijke
oorzaak van bevinding a.

Bijkomend: de 3,7 MB JSON wordt bij import volledig in geheugen geladen, en staat in een
Google Drive-map die tegelijk gesynchroniseerd wordt.

### 1.4 Twee agents die geen agent zijn

**De Archival Alignment Agent (ADR-007) doet geen inhoudelijke analyse.** Het rapport zegt
"Geanalyseerd door: archief-alignment-check (Claude 3.5 Sonnet)" en de code-comment zegt
"Claude 3.5 Sonnet logica", maar er is geen modelaanroep. De volledige detectie is
`archival_validator.py:60`:

```python
if match["score"] < 0.25 and len(historical_matches) > 1:
```

Een **lage** gelijkenisscore wordt gerapporteerd als inhoudelijke tegenstrijdigheid. Dat is
de logica omgekeerd: een lage score betekent dat de passage niets met het stuk te maken
heeft. De gate gaat willekeurig af, altijd op de minst relevante treffers, en dwingt vlak
voor deploy tot een keuze "voortschrijdend inzicht of inhoudelijke fout" over een passage
die geen van beide is. Zo'n gate wordt binnen drie posts weggeklikt.

**De Socratische chat (Modus 1) is een mock.** `brainstorm.py:_generate_socratic_reply` telt
berichten en geeft drie vaste strings terug. De `SOCRATIC_SYSTEM_PROMPT` bovenaan het bestand
wordt nergens gebruikt. `briefing.md` wordt gevuld met de eerste drie dingen die de auteur
typt, onder kopjes die suggereren dat er analyse heeft plaatsgevonden. Sessies staan in een
in-memory dict: server herstart of tweede worker en de brainstorm is weg.

### 1.5 Web, veiligheid en hygiëne

- `web/app.js` en `web/app_v2.js` zijn **byte-identiek** (793 regels elk); `index.html:350`
  laadt alleen v2. De cache-workaround uit commit `179b84b` staat er als permanente duplicatie.
- Drie stapelende oplossingen voor hetzelfde cacheprobleem: no-store middleware
  (`server.py:29`), cache-busting query's, en een inline fail-safe in de HTML.
- **Security blokkeert centraal hosten.** `allow_origins=["*"]` met `allow_credentials=True`
  (ongeldige combinatie), en van alle endpoints is er precies één beveiligd
  (`reindex-async`). Open staan: `init`, `run`, `complete`, `approve`, `reject`, `flags`,
  `repair`, `resolve-alignment`. Met het WP-token in `.env` op dezelfde machine.
- `pytest` staat niet in `requirements.txt` en niet in `.venv`; de drie testbestanden
  (1090 regels) draaien op dit moment niet.
- `ADMIN_TOKEN` en `admin_token` staan allebei in het template; `server.py:389` leest beide.

---

## 2. Plan

### Dwingende volgordes

- Blok A2 (index repareren) vóór A3 (RAG aansluiten), anders sluit je agents aan op een
  index zonder drafts.
- Blok D (auth) vóór blok C (centraal draaien), anders staat er een open schrijf-API op
  internet met het WP-token ernaast.
- Blok B en blok C route A delen dezelfde infrastructuur: een modelaanroep vanuit Python.
  Kies je route A, dan valt B er grotendeels in.

### Blok 0 — Stabiliseren

Geen nieuwe functionaliteit. Zonder dit meet je later niets.

| Actie | Bestand |
|---|---|
| `pytest` toevoegen en installeren, tests draaien als baseline | `requirements.txt` |
| `web/app.js` verwijderen | `web/` |
| `ADMIN_TOKEN` / `admin_token` ontdubbelen | `.env_template`, `server.py:389` |
| Eenmalige `rag_cli.py reindex --purge` | — |

**Verificatie:** tests groen; `rag_cli.py status` toont ~13 lokale slugs naast de 58
WP-slugs; `draft.md` verschijnt in de filename-verdeling.

### Blok A — De RAG bruikbaar maken

**A1. Indexeren correct maken** (`rag_archive.py`)

- Per-slug-skip vervangen door mtime-vergelijking per bestand.
- Bij herindexeren van een bron eerst de oude chunks van die bron verwijderen, in plaats van
  dedupliceren op `chunk_id`.
- Tombstoning: slugs die niet meer op schijf of op de site staan verwijderen.
- De volledige herindexering uit `validate_archival_alignment:24` halen.
- `threading.Lock` op de singleton, of de module-level singleton vervangen door een instantie
  die de service beheert.

**A2. IDF toevoegen** (`rag_archive.py`, `_tokenize` en `search`)

Document frequencies één keer berekenen bij `save_index` en meeschrijven in het indexbestand.
Circa twintig regels.

Daarna: het woord "semantisch" uit de endpoint-docstring halen en ADR-006 bijwerken, óf de
embeddings alsnog bouwen. Ontwerp en implementatie moeten weer hetzelfde zeggen.

**A3. Aansluiten op de agents** (`briefs.py`, `.claude/agents/`)

De eigenlijke oplevering. In `briefs.py` een verplichte openingsstap in elke
onderzoekersbrief en in de reeks-consistentie-brief:

```
python3 scripts/rag_cli.py search "<onderwerp>" --top-k 12
```

En in `blogpost-onderzoeker.md:19` het woord "later" schrappen.

**A4. Eenmalige corpusinventarisatie**

`reference/corpus-inventaris.md` over alle 61 posts: id, datum, titel, kernbegrippen, en
welk reeksdeel eraan raakt. Vangnet onder de RAG, want lexicaal zoeken vindt
"stroomopwaarts" wel maar "de controle naar voren halen" niet.

**Verificatie:** zoekopdracht op "intentie" levert `?p=211`, `?p=219` en `?p=251` op; een
lokale draft is vindbaar in de index.

### Blok B — De nep-agents

**B1. Alignment-gate** (`archival_validator.py`) — **afgerond 2026-08-14, route gewijzigd**

Dit blok stelde voor de modelaanroep vanuit Python te doen (`anthropic` in
`requirements.txt`, `ANTHROPIC_API_KEY` in `.env`). Bij de uitvoering is gekozen voor de
**subagent-route**: `.claude/agents/archief-consistentie-check.md` beoordeelt en schrijft
`archief-consistentie.md`; `archival_validator.py` leest alleen nog het verdict. Reden:
dat is dezelfde constructie als stijl-check, bron-check en reeks-consistentie, dus één
uitvoeringspad in plaats van twee, en geen API-sleutel of extra dependency.

Uitgevoerd: de regel `score < 0.25` is weg, de misleidende "Claude 3.5 Sonnet"-vermelding
is weg, de eis van een geciteerd paar wordt afgedwongen door `complete alignment`, en de
gate is voorwaardelijk hard (zonder bevinding schuift hij door, met bevinding stopt hij ook
in yolo). Zie ADR-007 §4.

Onderweg gevonden en gerepareerd: in de discrepantie-tak werd `state["phase"]` niet op
`alignment` gezet. De Web UI toonde de keuzeknoppen daardoor juist níet bij een gevonden
discrepantie — de enige uitkomst waarvoor de gate bestaat, liep vast.

De keuze voor Sonnet 5 blijft staan; die zit nu in de `model:`-regel van de agentdefinitie.

**B2. Socratische chat** (`brainstorm.py`)

Verwijderen tot blok C beslist is. Nu is het een mock die een `briefing.md` produceert die
eruitziet als analyse maar alleen de eigen invoer bevat, en de rest van de keten vertrouwt
dat bestand. Zodra er een modelaanroep-pad is: echt maken met de bestaande
`SOCRATIC_SYSTEM_PROMPT`, en sessies naar schijf in plaats van een in-memory dict.

### Blok C — De execution plane

De enige echte beslissing in dit plan.

**C1. ADR-010 schrijven** met de twee routes tegen elkaar. Ontbreekt volledig in de negen
bestaande ADR's, terwijl het de kern van het doel is.

**C2. Implementeren.** Aanbevolen: **route B, headless Claude Code op een altijd-aan
machine.** Hergebruikt de negen bestaande agentdefinities en de skill zonder duplicatie, de
menselijke gates blijven zoals ze zijn, klaar in dagen. Concreet: kleine altijd-aan machine,
repo erop, een worker die pollt op posts met `status: running`, de bijbehorende `agent_brief`
uitvoert via `claude -p`, en daarna `complete` aanroept. De web-UI verandert niet.

Alternatief: route A, Agent SDK server-side. Nettere eindtoestand, maar elke agent wordt twee
keer onderhouden tenzij de `.claude/agents/*.md` bestanden als gedeelde bron worden geparsed.

**Randvoorwaarde bij beide routes:** de repo uit Google Drive halen en git als synchronisatie
gebruiken. Twee machines die tegelijk in een gesynchroniseerde map `state.json` en een 3,7 MB
index schrijven gaat mis.

### Blok D — Veilig centraal

Moet af zijn vóór C2 iets publiek benadert.

- Auth-middleware op alle muterende endpoints.
- `allow_origins` van `["*"]` naar één origin.
- De drie stapelende cache-oplossingen terugbrengen tot één.

### Volgorde

```
Blok 0 → Blok A → B1 stap één → Blok D → Blok C → Blok B rest
```

Blok D vóór C omdat het goedkoop is en anders vergeten wordt zodra de eerste centrale deploy
verleidelijk wordt. B1 stap één vroeg omdat het één regel uitzetten is.

Blok 0 en blok A horen in één sessie: samenhangende wijziging, klein contextbeslag, één
duidelijk verificatiecriterium.
