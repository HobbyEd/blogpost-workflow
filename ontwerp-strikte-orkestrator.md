# Ontwerp: strikte orkestrator

*Control plane in code. Content plane blijft LLM. Mens-gates blijven, maar fasevolgorde is niet meer optioneel.*

Status: v1 gebouwd (juli 2026). Auteur: Edwin van Dillen, samen met Grok Build.

Gerelateerd: `ontwerp-uitgangspunten-blogpost-workflow.md` (oorspronkelijke brief),
`scripts/orchestrate.py` (implementatie), `templates/state.template.json`.

---

## 1. Probleem

De blogpost-workflow is inhoudelijk volwassen (subagents, scripts, huisstijl, deploy
als concept). De **orkestratie** liep via een lange skill-prompt op de main thread.
Gevolg in productie:

- `state.md` raakt uit sync (`huidige_fase` vs. fasentabel vs. bestanden op schijf).
- Stappen worden overgeslagen of omgewisseld zonder named exception (deel 5: visuals
  en deploy vóór herstelde Grok-kritiek; synthese open terwijl concept al live als draft).
- De LLM mag "behulpzaam" de keten sturen; consistentie hangt van medewerking af.

Harde effecten (WordPress alleen `status: draft`) zaten al in code. De volgorde niet.

## 2. Doel

1. **Eén machine-leesbare waarheid** per post over fase, status, flags en artefacten.
2. **Expliciete transitiegrafiek**: alleen toegestane stappen; de rest faalt hard (exit ≠ 0).
3. **Preconditions / postconditions** op bestanden en flags.
4. **Named exceptions** (`skip_synthesis`, `defer_critique`) i.p.v. stille omwegen.
5. **Dunne skill/host**: Claude Code of Grok Build roepen de CLI aan; zij verzinnen geen fase.
6. **Host-agnostische control plane**: Python + stdlib, zelfde stijl als `deploy_post.py`.

Niet-doel van v1: agents zelf spawnen via API. Content-stappen blijven handmatig of via
chat-host; de orkestrator zegt *wat* mag en *of* het artefact klopt.

## 3. Twee lagen

| Laag | Verantwoordelijkheid | Eigenaar |
|------|----------------------|----------|
| **Control plane** | Volgorde, pre/post, gates, log, doctor | `scripts/orchestrate.py` + `state.json` |
| **Content plane** | Outline, draft, checks, Grok, visuals | Subagents / LLM + `scripts/render_svg.py` / MCP |

De skill (`blogpost-workflow`) wordt op termijn een schil: `status` → voer agent-brief
uit → `complete` → bij gate vraag mens → `approve` / `reject`.

## 4. State-formaat

### 4.1 `state.json` is de bron van waarheid

v1 kiest **JSON**, niet YAML:

- Alleen Python-stdlib (zelfde constraint als deploy/render).
- Geen parse-ambiguïteit.
- Eenvoudig te valideren en te diffen.

Pad: `posts/<slug>/state.json`.

Menselijk logboek: `state.md` mag blijven bestaan (import, beslislog, reeks-context).
De CLI **leest geen fase meer uit markdown** nadat `state.json` bestaat; wel kan
`import-md` een eerste `state.json` afleiden, en `render-md` een projectie schrijven.

Template: `templates/state.template.json`.

### 4.2 Velden (v1)

```text
schema_version: 1
slug, titel, aangemaakt
yolo_mode: bool
phase: intake | outline | draft | style | series | critique | synthesis | visuals | deploy | done
status: ready | running | waiting_gate | blocked | done
artefacts: { outline, draft, grok_feedback, synthese, visuals, wp_post_id, edit_url }
flags: { skip_synthesis, defer_critique, deploy_approved }
gate: { pending, last_decision }   # pending null of phasenaam
blocked_reason: string|null
log: [ { at, event, phase?, note? } ]
```

Artefact-status op schijf wordt bij `doctor` / `complete` gecontroleerd; de JSON
houdt afgeleide velden bij (`wp_post_id`, `edit_url`) en vlaggen of een stap
functioneel klaar is.

### 4.3 Fasen vs. oude skill-nummers

| phase (JSON) | Oude skill-fase | Artefact |
|--------------|-----------------|----------|
| intake | 0 | map + state |
| outline | 1 | outline.md |
| draft | 2 | draft.md |
| style | 2b | (rapport; draft blijft) |
| series | 2c | (rapport; draft blijft) |
| critique | 3 | grok-feedback.md |
| synthesis | 4 | synthese.md |
| visuals | 5 | visuals/* + refs in draft |
| deploy | 6 | wp_post_id + edit_url |
| done | — | pipeline af |

## 5. Transitiegrafiek

### 5.1 Lineaire default

```text
intake → outline → draft → style → series → critique → synthesis → visuals → deploy → done
```

Per content-fase (outline … deploy):

1. `status=ready` → `run <phase>` → `status=running` (+ agent-brief).
2. Content-werk buiten de CLI (agent of script).
3. `complete <phase>` → postconditions → `status=waiting_gate` (of yolo, zie 5.3).
4. `approve` → volgende phase, `status=ready` (of `done` na deploy).
5. `reject` → terug `status=ready` op dezelfde phase (opnieuw draaien).

Intake is direct `complete` bij `init` (map aangemaakt); eerste gate is optioneel
bevestiging van slug/titel (`waiting_gate` na init, of meteen outline-ready).

### 5.2 Gate-types

| Gate na complete van | Type | Yolo mag auto-approve? |
|----------------------|------|-------------------------|
| outline, draft, style, series, critique, visuals | soft | ja |
| synthesis | hard (redactionele keuzes) | nee |
| deploy | hard (extern effect) | nee |

`deploy` mag alleen `run`/`complete` als `flags.deploy_approved == true`. Die vlag
zet je met `approve --deploy` (of `set-flag deploy_approved true` na bewuste gate).

### 5.3 Yolo

Als `yolo_mode` en de gate soft is: na geslaagde `complete` automatisch `approve`
en door naar de volgende phase `ready`. Harde gates stoppen altijd.

Chaining van meerdere soft stappen in één CLI-aanroep is **niet** v1: de host
roept herhaaldelijk `next` / `run` / `complete` aan. De state machine garandeert
alleen dat elke stap legaal is.

### 5.4 Named exceptions (flags)

| Flag | Effect |
|------|--------|
| `skip_synthesis` | Na approve van critique: volgende phase is `visuals`, niet `synthesis`. |
| `defer_critique` | Staat toe `run visuals` terwijl critique nog niet gereed is; critique blijft open tot later. Doctor waarschuwt. |
| `deploy_approved` | Verplicht voor `run deploy` / `complete deploy`. |

Illegale sprongen zonder flag → exit 2, state ongewijzigd (behalve optionele log bij
bewuste `set-flag`).

### 5.5 `blocked`

Als `complete` faalt op postconditions (bestand ontbreekt, leeg, Grok-fout):
`status=blocked`, `blocked_reason=...`. Herstel: fix artefact, dan `complete`
opnieuw, of `reject` om opnieuw `run` te doen, of `set-status ready` (alleen repair).

### 5.6 Statustabel (afgeleid, nooit opgeslagen)

Edwin wil per post in één oogopslag zien welke fase gereed/bezig/open is (juli 2026,
bij de start van deel 7). De verleiding is een tabel bij te houden in `state.md`,
zoals vóór v1 — maar dat is precies het driftprobleem dat v1 oploste.

In plaats daarvan berekent `table` de tabel bij **elke aanroep** uit `state.json` +
`probe_artefacts()` (dezelfde probe als `doctor`): fases vóór de huidige phase-index
zijn `gereed`, de huidige fase toont de live `status` (bezig/wacht op gate/geblokkeerd),
fases erna zijn `open`. `skip_synthesis` en `defer_critique` krijgen een eigen label
(`overgeslagen`, `uitgesteld`) in plaats van fout `gereed` te tonen. Er is geen
`table`-veld in `state.json`: de tabel is een view, geen bron van waarheid.

## 6. CLI (`scripts/orchestrate.py`)

```text
python3 scripts/orchestrate.py <command> [--post <slug>|--post-dir <pad>] [opties]
```

| Command | Functie |
|---------|---------|
| `init --slug ... --titel ...` | Map + state.json (+ optioneel yolo) |
| `status` | Fase, status, flags, next action (JSON of tekst) |
| `table` | Statustabel per fase (0–6), afgeleid uit state.json + schijf; markdown of `--json` |
| `next` | Precies één toegestane vervolgactie + agent-brief |
| `run <phase>` | Prechecks; zet running; print agent-brief |
| `complete <phase>` | Postchecks; waiting_gate of yolo-approve |
| `approve` | Gate akkoord; advance phase |
| `reject [--note ...]` | Gate afgewezen; opnieuw ready op zelfde phase |
| `set-flag <naam> true\|false` | Named exception / yolo |
| `doctor` | Drift: JSON vs. bestanden vs. flags |
| `import-md` | state.md (+ bestanden) → state.json |
| `render-md` | state.json → compacte state.md-projectie (optioneel) |
| `repair` | Artefacten scannen; phase/status voorstellen of --apply |

Exitcodes: 0 ok, 1 usage/IO, 2 illegale transitie of failed pre/post, 3 blocked/doctor hard fail.

## 7. Preconditions / postconditions (v1)

| Phase | Pre (`run`) | Post (`complete`) |
|-------|-------------|-------------------|
| outline | phase=outline, status=ready | outline.md bestaat, niet leeg |
| draft | outline.md present | draft.md bestaat, niet leeg |
| style | draft.md present | draft.md nog present (rapport zit in log/host) |
| series | draft.md present | draft.md present |
| critique | draft.md present; tenzij alleen deferred path | grok-feedback.md bestaat, niet leeg |
| synthesis | grok-feedback.md; niet als skip_synthesis | synthese.md bestaat, niet leeg |
| visuals | draft.md; critique gedaan **of** defer_critique | minstens één bestand in visuals/ |
| deploy | deploy_approved; draft.md; bij voorkeur visuals-stap gedaan of bewust overgeslagen later | wp_post_id + edit_url in state gezet via `complete deploy --post-id N --edit-url ...` |

`complete deploy` krijgt post-id/edit-url als argumenten (deploy-script blijft
bron van waarheid voor de upload; orkestrator legt alleen vast).

## 8. Agent-briefs

`run` en `next` printen een vast JSON-blok `agent_brief` met:

- `agent`: blogpost-onderzoeker | blogpost-schrijver | stijl-check | …
- `post_dir`, `inputs`, `outputs`
- `instruction`: één alinea voor de host/subagent

De orkestrator voert de agent niet uit (v1). De host mag geen andere phase starten
dan de brief noemt.

## 9. Migratie

1. Bestaande posts: `import-md --post <slug>` → `state.json`.
2. `doctor --post <slug>` → handmatig flags (`skip_synthesis`, etc.) waar de geschiedenis
   afwijkt van de lineaire default.
3. Nieuwe posts: alleen `init`.
4. Skill: stapsgewijs omzetten naar CLI-schil (niet blokkerend voor CLI-gebruik).

## 10. Los van Claude Code

| Component | Claude-gebonden? |
|-----------|------------------|
| `orchestrate.py`, `state.json`, deploy/render scripts | Nee |
| Subagent-prompts (`.claude/agents`) | Ja als host; inhoud is portable markdown |
| Grok-MCP-server | Nee (Python); host moet MCP of directe API aanbieden |
| Skill-orkestratie | Ja — wordt optionele schil |

**Conclusie:** v1 ontkoppelt de *keten* van Claude Code. Content-agents nog via een
host (Claude, Grok Build, of later API-runner). Volgende stap (niet v1): `Runner`
protocol dat `run outline` zelf een agent spawnt.

## 11. Bewust niet in v1

- Automatisch spawnen van subagents / API-calls.
- Yolo-auto-chain van meerdere phases in één process.
- RAG.
- Strikte JSON-Schema validatie via externe lib (handmatige checks volstaan).
- Verwijderen van `state.md` of herschrijven van de volledige skill.

## 12. Definition of done (v1)

- [x] Ontwerpdocument (dit bestand).
- [x] Template `templates/state.template.json`.
- [x] CLI met init, status, next, run, complete, approve, reject, set-flag, doctor, import-md, render-md, repair.
- [x] Smoke-test: init → run/complete/approve, yolo soft-advance, illegale deploy geweigerd (exit 2).
- [x] `import-md` + `doctor` op deel 4 (done), deel 5 (done + `skip_synthesis`), deel 6 (draft ready).
- [x] Skill nog niet verplicht omgeschreven; CLI is bruikbaar standalone (skill verwijst wel naar de CLI).

## 13. Gebruik (snel)

```bash
# Nieuwe post
python3 scripts/orchestrate.py init --slug mijn-post --titel "Werktitel"

# Bestaande post importeren
python3 scripts/orchestrate.py import-md --post anatomie-agents-5-anatomie-van-een-harness
python3 scripts/orchestrate.py doctor --post anatomie-agents-5-anatomie-van-een-harness

# Keten
python3 scripts/orchestrate.py next --post mijn-post
python3 scripts/orchestrate.py run outline --post mijn-post
# … agent schrijft outline.md …
python3 scripts/orchestrate.py complete outline --post mijn-post
python3 scripts/orchestrate.py approve --post mijn-post --note "outline ok"
```
