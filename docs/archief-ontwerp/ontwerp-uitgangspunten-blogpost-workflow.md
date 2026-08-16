# Ontwerpuitgangspunten blogpost-workflow

*Ontwerpdocument voor een gedeeltelijk geautomatiseerde workflow om blogposts voor edwinvandillen.nl te produceren. Dit document legt de uitgangspunten en de architectuur vast. Het dient als brief voor de bouw die erna volgt.*

Status: concept, juli 2026. Auteur: Edwin van Dillen, samen met Claude Code.

---

## 1. Doel

Het huidige schrijfproces is een vaste reeks stappen die grotendeels met de hand loopt. Onderwerp bepalen. Outline maken en verrijken. Paragrafen schrijven in huisstijl. Concept naar Grok voor kritiek. Kritiek terug voor synthese. Samen aanpassen. Visualisaties maken. Publiceren als concept in WordPress.

Die reeks is in de kern een prompt chain met beslismomenten voor de mens. Het doel is deze chain om te zetten in herbruikbare, reproduceerbare componenten. Elke stap wordt een agent of een skill. De overdracht tussen stappen wordt expliciet. Het resultaat is hervatbaar over meerdere sessies en goedkoper in gebruik.

Het doel is niet volledige automatisering. De beslismomenten die het proces nu sturen blijven behouden.

---

## 2. Uitgangspunten

**Chaining, geen monoliet.** Elke fase heeft één verantwoordelijkheid en levert een reviewbaar tussenartefact. De output van fase N is de input van fase N+1. Dit is hetzelfde patroon als beschreven in de post over prompt chaining.

**Mens in de lus per gate.** Tussen elke fase staat een beslismoment. Doorgaan, bijsturen of opnieuw. Er wordt nooit stilzwijgend gepubliceerd.

**Model-tiering.** Elke component draait op het goedkoopste model dat de taak aankan. Een duur model (Opus) alleen waar oordeel en creatie zitten. Een goedkoop model (Haiku, Sonnet) voor patroonvolgend en mechanisch werk. Bewust tokenbeheer is hier een ontwerpparameter, niet een optimalisatie achteraf.

**Hervatbare staat.** Per blogpost een werkmap met een `state.md`. Dat manifest legt vast in welke fase de post zit en welke artefacten klaar zijn. Het is de gestructureerde opvolger van de losse overdrachtdocumenten die nu ad hoc worden gemaakt.

**Hergebruik het bestaande.** Publiceren gebeurt via de bestaande deploy-scripts. Visuals volgen het kleurpalet en de SVG-conventies die al in de bovenliggende `CLAUDE.md` en de presentatie-skill staan. Er worden geen wielen opnieuw uitgevonden.

**Stijl als controleerbare stap.** De huisstijlregels zijn geen impliciete verwachting. Ze worden een aparte controlestap. Geen gedachtestreep. Geen superlatieven. Korte zinnen. Een bron bij elke scherpe claim.

**Vervangbare contextophaling.** De stap die context uit eerdere posts haalt, wordt als losse, vervangbare component ontworpen. Nu leest die stap de eerdere posts direct in. Later wordt dat een query op een kleine RAG-index over de bestaande posts. De rest van de keten verandert daarbij niet.

---

## 3. Architectuur

Eén orkestrator-skill leidt de keten. Die skill leest `state.md`, bepaalt de volgende gate en roept de juiste subagent of skill aan. De mens bevestigt elke overgang.

| Fase | Component | Type | Model | Doet |
|------|-----------|------|-------|------|
| 0 Intake | `blogpost-workflow` | orkestrator-skill | Opus (main thread) | onderwerp uitvragen, werkmap en `state.md` aanmaken, backlog raadplegen |
| 1 Outline en verrijking | `blogpost-onderzoeker` | subagent | Opus | onderwerp tegen eerdere posts leggen, zoeken naar theorie en voorbeelden, outline met bronnen |
| 2 Draft schrijven | `blogpost-schrijver` | subagent | Sonnet | paragrafen in huisstijl op basis van de outline |
| 2b Stijl-controle | `stijl-check` | skill | Haiku | controle op gedachtestreep, superlatieven, zinslengte en bron-bij-claim |
| 3 Kritiek | `grok-reviewer` | subagent plus Grok-MCP | subagent op Haiku, kritiek door Grok | concept naar Grok met vaste kritische persona, ruwe kritiek terug |
| 4 Synthese | `blogpost-onderzoeker` (hergebruik) | subagent | Opus | Grok-feedback analyseren, voorstel voor aanpassingen, mens beslist |
| 5 Visuals | `blogpost-visuals` | skill | Sonnet | minimale en ondersteunende visuals voorstellen, SVG maken met paletregels, PNG-conversie |
| 6 Deploy | `blogpost-deploy` | skill | Haiku of script | markdown naar HTML, media-upload, concept via WordPress REST |

De denk-intensieve stappen blijven op Opus. Alles wat patroonvolgend of mechanisch is zakt naar Sonnet of Haiku. Zo is het uitbesteden van werk aan een goedkoper model in de architectuur ingebouwd.

---

## 4. Grok via MCP

De kritiekstap loopt via een kleine lokale MCP-server op de xAI-API. Die API is OpenAI-compatibel en bereikbaar op `https://api.x.ai/v1`. De server biedt één tool: `grok_review(text, focus)`.

De kritische rol die nu met de hand in de Grok-builder wordt ingesteld, komt in een versie-beheerde systeemprompt. Het voordeel ten opzichte van kopiëren en plakken is drieledig. De reviewer is reproduceerbaar. De prompt staat onder versiebeheer. De subagent kan de aanroep zelf doen.

De API-key komt uit een omgevingsvariabele (`XAI_API_KEY`). De key staat niet in de repo.

---

## 5. Staat, mappen, git en RAG

Per post een werkmap onder `01. Blogpost agents/<slug>/`. Daarin `state.md`, `outline.md`, `draft.md`, `grok-feedback.md`, `synthese.md`, een map `visuals/` en een `publish.log`.

**Git-scheiding.** De workflow-code, de agents en de skills komen onder versiebeheer. De blogposts zelf niet. Deze scheiding wordt vastgelegd via `.gitignore` of via aparte mappen. Edwin richt de git-repo van de werkmap zelf in.

**RAG als vervolg.** In een latere fase komt een kleine RAG-index over de reeds geschreven posts. De onderzoeker-fase ruilt dan zijn directe inlees-actie om voor een query op die index. De interface van die fase wordt nu al zo ontworpen dat deze omruil mogelijk is zonder de rest van de keten te raken.

---

## 6. Gefaseerde bouw

**Fase A. Skelet en meeste denkkracht.**
De orkestrator-skill, de onderzoeker-subagent en de stijl-controle. Op dit punt is de workflow bruikbaar tot en met een gecontroleerde draft.

**Fase B. Kritieklus.**
De Grok-MCP-server en de reviewer-subagent. De onderzoeker wordt hergebruikt voor de synthese.

**Fase C. Visuals en publiceren.**
De visuals-skill en de deploy-skill. De schrijver wordt als aparte Sonnet-subagent afgesplitst voor kostenoptimalisatie van fase 2.

---

## 7. Openstaande punten

- Een xAI API-key beschikbaar maken (`XAI_API_KEY`) voor fase B.
- De Grok-modelnaam kiezen. Een sterker model voor scherpere kritiek tegenover een goedkoper model voor lagere kosten.
- De vorm van de RAG-index bepalen op het moment dat fase A staat. Type embeddings, opslag en de query-interface.

---

## 8. Status van de bouw (bijgewerkt 13 juli 2026)

De secties 1 tot en met 7 hierboven zijn de oorspronkelijke brief. Deze sectie legt
vast wat er sindsdien daadwerkelijk is gebouwd en getest, en wat nog openstaat.

### Fase A — gebouwd en getest

Alle workflow-code staat onder `01. Blogpost agents/.claude/` (geversioneerd).

- `skills/blogpost-workflow/SKILL.md` — orkestrator (Opus, main thread), intake +
  gate-logica. Inmiddels uitgebreid met fase 3 en 4 (zie Fase B).
- `skills/blogpost-workflow/templates/state.template.md` — staat-manifest per post.
- `agents/blogpost-onderzoeker.md` — subagent (Opus), outline + bronnen, met het
  "vervangbare contextophaling"-blok als voorbereiding op RAG.
- `agents/stijl-check.md` — subagent (Haiku).
- `.gitignore` — negeert `posts/` (per-post-werkmappen) en `.env`.

Twee ontwerpbijstellingen t.o.v. de tabel in sectie 3:
- **Model-tiering loopt via subagents, niet via skills.** Een skill erft het model van
  de aanroepende context; alleen een subagent heeft een eigen `model`-veld. `stijl-check`
  is daarom een subagent (Haiku), geen skill. Dezelfde redenering geldt straks voor de
  visuals- en deploy-stappen in Fase C.
- **`stijl-check` is gesplitst** na een testbevinding: Haiku miste een em-dash toen die
  puur op modeloordeel werd gecontroleerd. Nu doet de subagent de lexicale checks
  (em-dash, uitroepteken, emoji) deterministisch via Grep, en alleen de oordeelschecks
  (superlatieven, zinslengte, bron-bij-claim) op het model.
- De per-post-werkmappen zitten onder `posts/<slug>/` (containermap), zodat de
  git-scheiding één regel is.

### Fase B — gebouwd en getest

- `.claude/mcp/grok_review_server.py` — MCP-server (stdio, JSON-RPC, alleen Python-
  stdlib), tool `grok_review(text, focus)`. Laadt de key uit `.env` en de persona uit
  het bestand hieronder.
- `.claude/mcp/grok-reviewer-persona.md` — de versie-beheerde kritische systeemprompt.
- `.mcp.json` (projectroot) — registreert de server als `grok`.
- `agents/grok-reviewer.md` — subagent (Haiku), roept `mcp__grok__grok_review` aan en
  schrijft de ruwe kritiek naar `grok-feedback.md`.
- Fase 4 (synthese) hergebruikt `blogpost-onderzoeker` (Opus): weegt de kritiek en
  schrijft een aanpasvoorstel naar `synthese.md`. De mens beslist per punt.

Concrete configuratie:
- De Grok-key staat in `.env` als `GROK_API_KEY` (of `XAI_API_KEY`).
  `.env` is gitignored.
- De WordPress credentials staan in `.env` als `WP_APPLICATION_TOKEN`, `WP_USERNAME` en `WP_SITE_URL`;
  het deploy-script (`scripts/deploy_post.py`) leest ze daar.
- Model: **`grok-4.3`** (default in de server; te overschrijven met `GROK_MODEL` in
  `.env`).

De hele keten is end-to-end getest op de testpost `posts/cynefin-agent-autonomie/`
(intake → outline → draft → stijl-check → Grok-review → synthese). De draft van die
testpost is bewust niet afgewerkt; hij dient als voorbeeld en bevat nog een open
gate-keuze (mag een agent in een complex domein zelfstandig probes uitvoeren).

### Autonomie-modus (yolo) — toegevoegd 13 juli 2026

De checkpoint-gated autonomie uit sectie 2 is instelbaar gemaakt per post via een
`yolo_mode`-vlag in `state.md` (standaard `uit`). De vlag zit op de **actie**, niet op
de fase: een stap mag in yolo zelfstandig draaien als hij **safe-to-fail** is —
omkeerbaar (bestand/git terug te draaien), begrensd tot `posts/<slug>/`, en
waarneembaar (levert een reviewbaar artefact). Dat geldt voor alle
artefact-genererende stappen en mechanische stijlcorrecties.

Twee soorten stappen blijven **altijd** een harde gate, ook in yolo: publiceren/deploy
(onomkeerbaar, naar buiten) en redactionele oordeelskeuzes (welke Grok-punten je
overneemt raakt Edwins betoog en stem). Het ontwerp valt één-op-één samen met de these
van de testpost: een echte safe-to-fail probe maakt autonomie verdedigbaar, omdat het
falen per constructie is ingedamd. Vastgelegd in `SKILL.md`, sectie "Modus: yolo of
voorstel", en in de state-template.

### Bijgewerkte openstaande punten

- xAI-key: geregeld. Model gekozen: `grok-4.3`.
- **De `grok`-MCP-server moet in Claude Code eenmalig worden goedgekeurd via `/mcp`.**
  Omdat `.mcp.json` na sessiestart is aangemaakt, verschijnt `grok` pas na een herstart
  van Claude Code in de lijst. Tot die goedkeuring bestaat de tool
  `mcp__grok__grok_review` niet in de sessie en kan de `grok-reviewer`-subagent hem niet
  aanroepen. **Opgelost/bevestigd 13 juli 2026:** na goedkeuring is de volledige
  subagentroute (`grok-reviewer` → `mcp__grok__grok_review` → `grok-feedback.md`) in een
  sessie succesvol end-to-end gedraaid op de testpost. De directe server-runner is niet
  meer nodig.
- RAG-index: nog te bepalen (ongewijzigd t.o.v. sectie 7).

### Fase C — gebouwd (13 juli 2026)

De visuals-, deploy- en schrijver-stappen zijn gebouwd. Conform de Fase A-bijstelling
zijn het **subagents** (eigen `model`-veld), niet skills zoals de tabel in sectie 3
aankondigde:

- `agents/blogpost-schrijver.md` — subagent (Sonnet). Splitst fase 2 af van de main
  thread: leest `outline.md` + huisstijl, schrijft `draft.md`. Verzint geen feiten
  buiten de outline.
- `agents/blogpost-visuals.md` — subagent (Sonnet), fase 5. Stelt spaarzaam visuals
  voor, maakt SVG's volgens het palet in `posts/<slug>/visuals/`, met PNG-conversie
  via headless Chrome (rsvg-convert ontbreekt op Windows).
- `agents/blogpost-deploy.md` — subagent (Haiku), fase 6. Zet markdown om naar HTML,
  uploadt PNG's en maakt de post aan als **concept** (`status: draft`) via de
  WordPress REST API (`?rest_route=`). Publiceert nooit live; dat blijft Edwins
  handmatige actie in wp-admin. Deze deploy-gate blijft hard, ook bij `yolo_mode: aan`.

`SKILL.md` stuurt nu fase 2 (schrijver), 5 (visuals) en 6 (deploy) aan; de
state-template heeft fase 5 en 6 als rijen.

**End-to-end getest op de testpost (13 juli 2026).** Fase 5: de visuals-subagent maakte
één SVG + PNG (1920×920) via headless Chrome. Fase 6: de deploy-subagent uploadde de PNG
(media-id 450) en maakte een WordPress-**concept** aan (post-id 451, `status: draft`).
Hard geverifieerd via een auth'd REST GET: status=draft, niet live — de deploy-gate
hield. Twee gotcha's uit fase 5 zijn teruggezet in `reference/deploy.md` en
`blogpost-visuals.md`: headless Chrome vereist absolute Windows-paden, en een
`linearGradient` met `objectBoundingBox` op een horizontale lijn rendert blanco (gebruik
`userSpaceOnUse`); controleer de PNG visueel, niet alleen op bestandsgrootte.

### Zelfstandige repo — loskoppeling van hogere mappen (13 juli 2026)

De workflow-code hing op meerdere plekken aan bestanden in de bovenliggende map
(`../CLAUDE.md` voor huisstijl en palet, `../deploy_naar_edwinvandillen_nl.md` voor
deploy, `../blogpost-*.md` en `../blogpost-backlog.md` voor context). Dat is
losgekoppeld zodat de repo zelfstandig kan bestaan:

- **Workflow-eigen kennis staat nu in de repo** onder `reference/`:
  `reference/huisstijl.md` (schrijfstijl + kalibratie + visuele identiteit) en
  `reference/deploy.md` (deploy-procedure, credentials uit `.env`, niet plaintext).
  Alle subagents en `SKILL.md` verwijzen hiernaar.
- **Het postcorpus komt van de live site**, niet van een naburige map. De onderzoeker
  haalt de laatste posts van edwinvandillen.nl via de WordPress REST API
  (`?rest_route=/wp/v2/posts&per_page=10&orderby=date`, WebFetch). Zo is er geen
  afhankelijkheid van een map op schijf; alleen internettoegang. Is de site onbereikbaar,
  dan levert de contextstap een lege context (geen fout). Later wordt dit een RAG-index
  over dezelfde posts; de in-/output van de stap blijft gelijk.
- **De backlog is optioneel en lokaal** (Edwins eigen planningsdocument, niet op de
  site). Er is geen standaardpad meer; zonder pad slaat de intake de backlog-suggesties
  over. Vastgelegd in `reference/externe-bronnen.md`, de enige plek waar externe naden
  staan.
- **Credentials in `.env`** (repo-root, gitignored): `GROK_API_KEY`, `WP_APPLICATION_TOKEN`, `WP_USERNAME` en `WP_SITE_URL`.

De secties 1–7 (de oorspronkelijke brief) noemen nog de oude opstelling; deze sectie 8
is de actuele waarheid.

### Deterministische stappen als scripts (13 juli 2026)

Na de eerste testrun bleek de deploy-subagent elke keer een Python-script te *schrijven*
voor de conversie en upload. Dat is duur in tokens en niet-deterministisch. Conform het
principe dat al bij de stijl-check (grep) en de Grok-server (MCP) is toegepast — mechanisch
werk hoort in code, niet in een LLM-aanroep — zijn de deterministische stappen nu vaste,
versie-beheerde scripts onder `scripts/`:

- **`scripts/deploy_post.py`** — markdown → **Gutenberg blok-markup** (niet klassieke HTML;
  eerdere posts staan als blokken en anders moet het in wp-admin met de hand worden
  omgezet), media-upload, en concept-post aanmaken/bijwerken. `status: draft` is hardgecodeerd;
  geen publiceer-optie. Getest: post-id 451 bijgewerkt naar echte blokken (paragraph, heading,
  list, table, image, separator). Een generieke md-library (pandoc/`markdown`) helpt niet —
  die levert klassieke HTML, geen blokken — dus een kleine stdlib-converter.
- **`scripts/render_svg.py`** — SVG → PNG via headless Chrome, met de absolute-paden-fix en
  grootte-verificatie ingebouwd.

De subagents zijn nu dunne orkestrators (optie 3 uit het overleg): `blogpost-deploy` (Haiku)
en `blogpost-visuals` (Sonnet) roepen het script aan en vangen fouten af; het model doet
alleen nog het oordeel (welke visual, waar in de tekst). De plaatsing van een beeld gebeurt
nu vóór de deploy: de visuals-stap zet de `![alt](visuals/…png)`-verwijzing in de draft, de
deploy-stap converteert die.

### Nog open

- RAG-index: nog te bepalen (ongewijzigd t.o.v. sectie 7).
- Aparte Sonnet-`blogpost-schrijver` (fase 2) is gebouwd maar nog niet op een echte
  post gedraaid; de schrijfkwaliteit t.o.v. de main-thread-draft is nog niet vergeleken.
- Opruimen: het WordPress-testconcept (post-id 451) en de test-media (id 450) staan op
  edwinvandillen.nl als concept. Verwijderen wanneer de testpost niet meer nodig is.

### Strikte orkestrator (v1, juli 2026)

De soft control plane (skill-prompt alleen) is aangevuld met een **harde control
plane** in code: `scripts/orchestrate.py` + `posts/<slug>/state.json`. Ontwerp:
`ontwerp-strikte-orkestrator.md`. Template: `templates/state.template.json`.

De skill blijft content-orkestratie (subagents aanroepen); fasevolgorde, pre/post
en named exceptions handhaaft de CLI. Content-agents worden in v1 nog niet door
de CLI gespawnd — dat is een latere runner-stap.
