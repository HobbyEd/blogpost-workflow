# Overdrachtsdocument — blogpost-workflow naar de web-app

**Van:** Claude (Claude Code, CLI-sessies augustus 2026)
**Voor:** Grok, die verder bouwt aan de web-app
**Datum:** 2026-08-16
**Repo:** `01. Blogpost agents`, branch `workflow-kwaliteitsverbetering` (18 commits, **niet** gemerged naar `main`)

Dit document beschrijft wat er staat, wat de ADR's vastleggen, waar de architectuur nu breekt, en welke drie stappen er voor liggen: ADR-analyse, de hele keten draaiend in een venv op de MacBook, en uiteindelijk in Docker op de Ubuntu-server.

Het is geschreven om zonder de voorgeschiedenis leesbaar te zijn. Waar ik iets niet zeker weet, staat dat er.

---

## 1. Wat dit systeem is

Een deterministische, agent-gebaseerde werkwijze om blogposts voor edwinvandillen.nl te schrijven. Eén post doorloopt elf fases, van intake tot deploy. Elke fase levert een artefact op schijf. De voortgang staat in één bestand.

Het systeem heeft twee helften, en het onderscheid is de kern van alles wat hierna komt:

| | Wat het is | Waar het draait | Status |
|---|---|---|---|
| **Control plane** | Toestandsmachine, gates, artefactcontrole, RAG | Python, deterministisch, geen LLM | Compleet en getest |
| **Execution plane** | De agents die daadwerkelijk schrijven, controleren, deployen | Claude Code op de laptop | **Bestaat niet als code** |

De web-app bedient op dit moment alleen de linkerhelft. Zie §5 — dat is het hoofdprobleem dat je gaat oplossen.

---

## 2. De repo

```
01. Blogpost agents/
├── server.py                    FastAPI, ~29 endpoints, dunne laag over WorkflowService
├── requirements.txt             fastapi, uvicorn, pydantic, httpx, python-dotenv, pytest
├── scripts/
│   ├── orchestrate.py           CLI: dezelfde functionaliteit als de API
│   ├── deploy_post.py           WordPress REST, levert altijd een CONCEPT
│   ├── haal_bron.py             bronnen ophalen incl. PDF-extractie
│   ├── rag_cli.py               index bouwen/zoeken
│   ├── render_svg.py            SVG → PNG via headless Chrome
│   ├── stijl_lexicaal.py        meetscript voor de stijl-check
│   ├── leesbaarheid.py          meetscript voor de leesbaarheid-check
│   └── orchestrator/            het hart (zie §3)
├── .claude/
│   ├── agents/                  10 subagent-definities (markdown, Claude Code-formaat)
│   └── skills/blogpost-workflow/SKILL.md    de orkestratie-instructie
├── web/                         index.html, app_v2.js, styles.css (vanilla JS, geen build)
├── templates/
├── adr/                         00 t/m 010 (009 is samengevoegd in 007)
├── reference/                   huisstijl.md, deploy.md, corpus-inventaris.md
├── tests/                       116 tests, alle groen
├── posts/<slug>/                werkmappen per post — GITIGNORED
└── .env                         secrets — GITIGNORED
```

### `scripts/orchestrator/` — de modules

| Module | Verantwoordelijkheid |
|---|---|
| `constants.py` | Fases, gate-typen, artefactnamen, blokindeling. Het domeinmodel. |
| `repository.py` | `state.json` lezen/schrijven, vingerafdrukken van de draft |
| `engine.py` | Toestandsovergangen, validatie bij afronden, gate-logica |
| `service.py` | `WorkflowService` — de publieke API die CLI én server gebruiken |
| `briefs.py` | Genereert de `agent_brief` per fase (tekst, geen uitvoering) |
| `probes.py` | Kijkt op schijf welke artefacten er zijn |
| `formatters.py` | Statustabellen voor terminal en UI |
| `verdicts.py` | Leest bevindingen uit controlerapporten, bundelt ze |
| `synthesis.py` | Synthese als beslismoment per punt |
| `revision.py` | Opmerkingen van de auteur na het lezen |
| `archival_validator.py` | Verdict van de archief-consistentie-agent |
| `rag_archive.py` | Lokale lexicale RAG (TF-IDF, geen embeddings) |
| `brainstorm.py` | De interactieve intake-fase |

**Belangrijk architectuurprincipe:** de CLI en de FastAPI-server zijn allebei dunne schillen om `WorkflowService`. Er zit geen logica in `server.py` die niet ook in `orchestrate.py` zit. Houd dat zo — het is de reden dat de testsuite betekenis heeft.

### Hoe je het nu draait

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q          # 116 passed
.venv/bin/python -m uvicorn server:app --reload --port 8000
.venv/bin/python scripts/orchestrate.py status <slug>
```

Python 3.14.4 lokaal. Eén waarschuwing in de tests (Starlette TestClient wil `httpx2`), verder schoon.

---

## 3. De keten

Elf fases plus `done`. Sinds ADR-010 gegroepeerd in drie blokken:

```
RICHTEN          intake → outline
BOUWEN           draft → style → series → critique → synthesis → visuals
OORDELEN         factcheck → alignment → deploy
```

Per fase: `run` → `complete` → `approve` of `reject`. `run` zet de status op `running` en geeft een briefing terug. `complete` controleert of het artefact bestaat en geldig is. Pas dan mag de gate open.

### Gate-typen

| Type | Fases | Gedrag |
|---|---|---|
| **Hard** | `intake`, `synthesis`, `deploy` | Altijd de mens. Geen uitzondering. |
| **Voorwaardelijk** | `style`, `series`, `factcheck`, `alignment` | Schuift door als er geen blokkerende bevinding is; stopt als die er wel is — ook in yolo-modus. |
| **Zacht** | `outline`, `draft`, `critique`, `visuals` | Mag automatisch door in yolo-modus. |

De voorwaardelijke gate is de belangrijkste vondst van ADR-010. Daarvóór moest een mens elf keer per post "akkoord" klikken; in de praktijk waren dat 49 goedkeuringen en nul afwijzingen. Een gate die altijd ja krijgt, is geen gate.

### Het bevindingenformaat

Elk controlerapport (`stijlcheck.md`, `reeks-check.md`, `feitencheck.md`, `leesbaarheid.md`) **moet** openen met een ```json-blok:

```json
{"findings": [
  {"severity": "blocking", "categorie": "misquote", "waar": "sectie 4",
   "wat": "Citaat wijkt af van de bron.", "suggestie": "..."}
]}
```

`severity` is `blocking` of `advisory`. Een lege lijst betekent: niets gevonden. Ontbreekt het blok of klopt het formaat niet, dan is de staat **`onleesbaar`** — nadrukkelijk niet "geen bevindingen". Zie §7, dat onderscheid heeft hier drie keer een bug veroorzaakt.

`alignment` gebruikt een eigen verdictformaat uit ADR-007; `verdicts.read_phase_findings()` vertaalt discrepanties daaruit naar blocking.

### De subagents

Tien definities in `.claude/agents/`. Deze zijn geschreven in het Claude Code-agentformaat (markdown met frontmatter: naam, beschrijving, toegestane tools). Ze zijn **niet** overdraagbaar naar een ander LLM zonder herschrijven:

`blogpost-onderzoeker`, `blogpost-schrijver`, `stijl-check`, `leesbaarheid-check`, `reeks-consistentie-check`, `grok-reviewer`, `blogpost-visuals`, `bron-check`, `archief-consistentie-check`, `blogpost-deploy`.

`grok-reviewer` is de enige die al een externe API aanroept, via de grok-MCP-server met `GROK_API_KEY`.

---

## 4. Analyse van de ADR's

Elf documenten in `adr/`. Hieronder per stuk wat het vastlegt, of het geïmplementeerd is, en waar het scheef staat. Dit is de eerste taak die Edwin noemde, dus lees ze zelf ook — dit is mijn oordeel, niet een vervanging.

| ADR | Titel | Status | Implementatie |
|---|---|---|---|
| 00 | Overall design web-UI & agentplatform | Accepted | Deels — beschrijft de UI die er is, plus een uitvoeringslaag die er niet is |
| 001 | Strict deterministic control plane in Python | Accepted | Volledig. Het sterkste deel van het systeem. |
| 002 | Modular orchestrator service package | Accepted | Volledig |
| 003 | Two-phase: interactieve brainstorm vs YOLO stepper | Accepted | Volledig, maar **achterhaald door 010** en niet bijgewerkt |
| 004 | Hard vs soft quality gates | Accepted | **Achterhaald door 010** en niet bijgewerkt |
| 005 | Bulk research protocol & source fetching | Accepted | Volledig (`haal_bron.py`) |
| 006 | Lokale RAG-vectorstore | **Proposed** | Volledig geïmplementeerd — status klopt niet meer |
| 007 | Archief-consistentie-agent & discrepantie-gate | Accepted | Volledig. Bevat sinds 2026-08-14 ook het samengevoegde 009. |
| 008 | Admin settings tab & background RAG-indexer | Accepted | Volledig |
| ~~009~~ | — | Samengevoegd in 007 | Nummer wordt niet hergebruikt |
| 010 | Workflow-topologie, gates en oordeelsmoment | Accepted | Volledig (zes stappen uit §6 zijn af) |

### Wat je moet weten voordat je erop bouwt

**ADR-003 en ADR-004 zijn verouderd.** Ze beschrijven de tweedeling hard/zacht en de yolo-modus zoals die vóór ADR-010 was. ADR-010 heeft daar een derde categorie tussen gezet (voorwaardelijk) en de fases in drie blokken gehergroepeerd. De *code* volgt 010; de ADR's 003 en 004 zijn niet bijgewerkt. Als je ze naast elkaar leest, lijkt de code fout. Dat is hij niet. Deze twee bijwerken staat op de openstaande lijst in ADR-010 §7.

**ADR-006 staat op Proposed terwijl de RAG volledig draait.** Alleen een statusfout.

**ADR-00 beschrijft een uitvoeringslaag die niet bestaat.** Dit is de gevaarlijkste, omdat het document overtuigend is. Zie §5.

**ADR-010 §7 somt op wat nog open is:**
- De afhankelijkheidsgraaf (alternatief C) is bewust niet gebouwd — de drie blokken zijn de eenvoudiger tussenstap.
- `synthesis` zit fysiek nog in Bouwen, terwijl het conceptueel bij Oordelen hoort.
- ADR-003 en ADR-004 bijwerken.
- Twee metingen die nog niet gedaan zijn: hoe vaak leidt Oordelen tot een revisieronde, en hoe vaak wordt een Grok-punt verworpen.

**ADR-011 is gereserveerd, nog niet geschreven.** Die moet de uitvoeringslaag vastleggen — precies wat jij gaat bouwen. Het verbeterplan (`docs/plan-kwaliteitsverbetering-workflow.md`, blok C) beschrijft de twee routes; §5 hieronder vat ze samen. Schrijf ADR-011 vóór of tijdens de implementatie, niet erna.

---

## 5. Het kernprobleem: er is geen uitvoeringslaag

**In de hele Python-codebase staat geen enkele LLM-aanroep.**

`WorkflowService.run_phase()` doet drie dingen: status op `running` zetten, loggen, en een `agent_brief` teruggeven — een string. Meer niet. Er is geen proces dat die briefing oppakt.

In de CLI ben ik dat proces. De `blogpost-workflow`-skill leest de brief, roept de juiste subagent aan, die schrijft `draft.md`, en daarna wordt `complete` aangeroepen. Die schakel zit volledig in de Claude Code-sessie en nergens in de repo.

Gevolg: **klik je in de web-UI op "run" bij `draft`, dan gebeurt er niets.** De state verschuift naar `running`, er ligt een briefing klaar, en daar blijft het. De web-UI is een afstandsbediening voor een toestandsmachine die zelf niets uitvoert.

Dit is niet stuk. Het is nooit gebouwd.

### De authenticatievraag

Edwin heeft een Claude-abonnement. De vraag die dit blokkeert: hoe gebruik je dat abonnement vanuit een web-app?

**Route B — headless Claude Code als worker. Gebruikt het abonnement.**

Een worker-proces draait in een lus:
1. vraag de server om posts met `status: running`
2. haal de `agent_brief` op
3. draai `claude -p "<brief>"` in de repo
4. roep `complete` aan

De authenticatie zit in de `claude`-CLI-installatie op die machine. Is die ingelogd met het Pro/Max-account, dan draait al het werk op het abonnement — geen aparte API-facturering. De tien bestaande subagent-definities en de skill werken ongewijzigd, want het is letterlijk dezelfde Claude Code.

Kosten: een machine die aan staat, en de rate limits van het abonnement.

**Route A — Agent SDK of Messages API server-side. Gebruikt het abonnement níet.**

De FastAPI-server roept Claude aan met een API-sleutel. Aparte factuur, per token. Technisch schoner (geen subprocess), maar de tien subagents moeten opnieuw gedefinieerd worden als SDK-agents, en er wordt betaald voor werk dat het abonnement al dekt.

**Het verbeterplan adviseert route B.** Dat advies staat, maar met één waarschuwing die zwaarder weegt naarmate je richting Docker gaat: zie §6.3.

### De harde regel voor de worker

De worker draait **alleen** fases die `run`-baar zijn. De gates blijven bij Edwin in de UI. De worker roept **nooit** `approve` aan.

Doe je dat wel, dan bouw je precies het ding terug dat ADR-010 heeft weggehaald: een keten die zichzelf goedkeurt.

---

## 6. De weg vooruit

### 6.1 Nu — venv op de MacBook

Doel: de hele keten draait lokaal end-to-end, gestart vanuit de web-UI, zonder dat een mens tussen `run` en `complete` hoeft te zitten.

Voorstel voor de eerste versie, bewust klein:

```bash
.venv/bin/python scripts/worker.py --once
```

Pakt één wachtende fase, draait hem, stopt. Zo zie je of de brief-in / artefact-uit-lus klopt vóórdat je er een lus omheen zet. Werkt dat, dan `--watch` met een interval, daarna pas launchd of systemd.

Punten om op te letten:
- De worker heeft de repo-root als werkdirectory nodig; `claude -p` moet de `.claude/`-map zien om de subagents en de skill te vinden.
- Foutafhandeling: wat als `claude -p` faalt of een leeg artefact oplevert? De fase moet dan naar `blocked`, niet stilletjes op `running` blijven staan. `complete` valideert al op artefactniveau — gebruik dat, vang de exception, en zet de reden in de state.
- Timeout per fase. Een schrijffase kan minuten duren; een vastgelopen fase mag de lus niet blokkeren.
- Eén fase tegelijk per post. Parallel draaien over meerdere posts kan later.

### 6.2 Daarna — Docker op de Ubuntu-server

Wat meeverhuist:
- FastAPI + uvicorn: probleemloos.
- De orchestrator: puur Python, geen systeemafhankelijkheden.
- `posts/` en de RAG-index: moeten op een **volume**, niet in het image. De index wordt herbouwd uit WordPress plus lokale bestanden, maar de postmappen zijn werk in uitvoering.
- `.env`: als secrets injecteren, niet in het image bakken.

Wat aandacht vraagt:
- **`render_svg.py` heeft een headless Chrome nodig.** Op de Mac zoekt het script een aantal bekende paden af. In een container moet Chromium mee in het image, of de visuals-fase draait ergens anders. Dit is de enige echte systeemafhankelijkheid in de repo.
- **`haal_bron.py`** heeft uitgaand netwerk nodig, en PDF-extractie mogelijk extra pakketten. Controleer de imports.
- **Tijdzone en `mtime`.** De RAG-indexer en de vingerafdruk-logica gebruiken bestandstijden. Een volume-mount over een netwerk kan daar rare dingen doen. De huidige postmap staat op Google Drive, wat al niet ideaal is.

### 6.3 Het openstaande risico: Claude Code op een headless server

Dit moet je vroeg uitzoeken, niet als laatste.

Route B leunt erop dat `claude` op de uitvoerende machine ingelogd is met het abonnement. Op de MacBook is dat triviaal. Op een headless Ubuntu-server in een container is dat een open vraag: hoe krijg je die login daar, en blijft hij geldig?

Ik weet niet zeker hoe dat precies uitpakt. Zoek dit uit voordat je het Docker-ontwerp vastlegt, want het antwoord bepaalt de architectuur:

- Lukt het — dan is route B de hele oplossing en gaat alles in één container.
- Lukt het niet — dan zijn er twee vormen. Ofwel de worker blijft op de MacBook draaien en praat met de server in Docker (de control plane in de container, de execution plane thuis). Ofwel je gaat alsnog naar route A met een API-sleutel, en accepteert de tokenkosten plus het herschrijven van de tien subagents.

De splitsing control plane in Docker / execution plane op de laptop is geen slecht tussenstation. Het maakt de scheiding uit §1 expliciet, en het is precies de scheiding die het systeem al heeft.

---

## 7. Valkuilen uit de praktijk

Eén patroon kwam deze maand vijf keer terug, en het is het waard om als toets te onthouden:

> **Iets meldt "in orde" terwijl het niets heeft gecontroleerd.**

Gevallen:
- De RAG-index zag er gevuld uit maar bevatte het verkeerde materiaal, doordat de testsuite hem overschreef (`index_path` stond vast bij import in plaats van afgeleid van `posts_root()`).
- `deploy_approved` overleefde een correctieronde: goedkeuring voor een tekst die daarna veranderd was.
- Een feitencheck van drie dagen oud gold als actueel voor een herschreven draft.
- De bevindingen-renderer meldde "Geen bevindingen" terwijl drie rapporten onleesbaar waren.
- De UI-badge stond op groen om dezelfde reden.

De oplossing was elke keer hetzelfde: **koppel een bewering aan bewijs.** Vingerafdrukken van `draft.md` (`repository.draft_fingerprint()`, `stale_phases()`), expliciete verdict-blokken, en aparte staten voor `onleesbaar` en `verouderd` naast `actueel`.

Als je iets bouwt dat een groen vinkje toont, vraag je af waar het bewijs voor dat vinkje vandaan komt.

### Verder

- **`posts/` en `graphify-out/` staan in `.gitignore`.** Postmappen zijn niet in git. Back-ups zijn Edwins verantwoordelijkheid.
- **Deploy levert altijd een concept.** `deploy_post.py` heeft geen publish-optie. Live zetten is handwerk in wp-admin. Dat is opzet — niet "opgelost" met een flag.
- **WordPress REST gaat via `?rest_route=`, niet `/wp-json/`.** Op deze host werkt het andere pad niet. Lees `reference/deploy.md` vóór je iets aan deployment verandert.
- **Openstaand: `deploy_post.py` overschrijft het concept.** Bewerkt Edwin in wp-admin terwijl hij leest, dan gaat dat verloren bij de volgende deploy. Werkafspraak nu: niet in wp-admin bewerken tijdens het lezen. Dit hoort een keer echt opgelost te worden.
- **`reference/huisstijl.md` is de enige bron van waarheid voor schrijfstijl.** Er stond ooit een kopie in `CLAUDE.md`; die liepen uiteen. Niet opnieuw dupliceren.
- **De UI had een tweede implementatie van de statustabel** die afweek van de orchestrator. Nu opgelost: `get_post_detail` vult `markdown_table` uit `service.get_table()`. Bouw geen tweede waarheid in JavaScript.

---

## 8. Staat van de branch

`workflow-kwaliteitsverbetering`, 18 commits, niet gemerged. Merge kan met:

```bash
git checkout main && git merge --ff-only workflow-kwaliteitsverbetering
```

Wat erin zit: de zes stappen uit ADR-010 §6 (blokindeling, bevindingenformaat, gebundelde bevindingen, actualiteitscontrole, synthese als beslismoment, revisiepunten), de RAG-herbouw, de samenvoeging van ADR-009 in 007, en ADR-010 zelf.

Eén post staat halverwege: deel 2 van de intentie-reeks, gedeployed als WordPress-concept 512, wachtend bij de deploy-gate. De stijl-, reeks- en feitencheckrapporten daarvan zijn van vóór het verdictformaat en lezen dus als `onleesbaar`. Dat is correct gedrag, geen bug.

---

## 9. Wat ik zou aanraden, in volgorde

1. **Lees de ADR's zelf**, met §4 als kaart. Werk 003, 004 en 006 bij zodat papier en code weer samenvallen. Dat is een uur werk en het voorkomt dat je op een verkeerd model bouwt.
2. **Zoek §6.3 uit** — Claude Code-authenticatie op een headless machine. Dit bepaalt de architectuur, dus doe het vóór het ontwerp, niet erna.
3. **Schrijf ADR-011** voor de uitvoeringslaag, met de uitkomst van 2 erin.
4. **Bouw `scripts/worker.py --once`** en draai hem op een echte post in de venv.
5. **Dan pas Docker.**

De verleiding is om meteen naar de container te gaan. De keten heeft alleen nog nooit één fase autonoom gedraaid. Doe dat eerst op de machine waar alles al werkt.

---

*Vragen over hoe iets bedoeld is: de ADR's gaan vóór de code, en `reference/` gaat vóór de ADR's als het over schrijfstijl of deployment gaat.*
