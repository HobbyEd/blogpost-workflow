---
name: blogpost-workflow
description: Orkestreert het schrijven van een blogpost voor edwinvandillen.nl als een hervatbare keten met een mens-gate tussen elke fase. Gebruik deze skill zodra Edwin een nieuwe blogpost wil beginnen, een bestaande post wil voortzetten, of zegt "nieuwe post", "blogpost schrijven", "post voor edwinvandillen.nl", "ga verder met de blogpost" of "waar stonden we met die post". De harde control plane is scripts/orchestrate.py + posts/<slug>/state.json (nooit fase verzinnen uit state.md). De skill roept subagents aan volgens next/run/complete/approve: outline (onderzoeker), draft (schrijver), stijl-check plus leesbaarheid-check, reeks-consistentie, Grok-kritiek, synthese, visuals, bron-check, deploy-concept. yolo_mode en named exceptions lopen via de CLI; publiceren blijft handmatig in wp-admin.
---

# Blogpost-workflow — orkestrator

Deze skill zet het schrijfproces voor edwinvandillen.nl om in een reproduceerbare
keten. Elke fase heeft één verantwoordelijkheid en levert een reviewbaar
tussenartefact. Tussen fasen staan mens-gates. Er wordt nooit stilzwijgend
gepubliceerd (live).

**Belangrijk:** jij (de main-thread agent) bent de *host* die content-subagents
aanroept. De *control plane* is code. Verzin geen fasevolgorde.

Zie ook: `ontwerp-strikte-orkestrator.md`.

## Control plane — verplicht, bij elke aanroep

Bron van waarheid: `posts/<slug>/state.json`, beheerd door:

```bash
python3 scripts/orchestrate.py <command> --post <slug>
```

### Bij start van de skill (altijd eerst)

1. Bepaal of dit een **nieuwe** post is of een **lopende** (`posts/<slug>/`).
2. **Lopend, wel `state.md` maar geen `state.json`:**
   `python3 scripts/orchestrate.py import-md --post <slug>`
3. **Lopend, wel `state.json`:**
   `python3 scripts/orchestrate.py status --post <slug>`
   en `python3 scripts/orchestrate.py next --post <slug>`
   (bij drift-warnings: `doctor`, eventueel `repair --apply` na akkoord van Edwin).
4. Voer **alleen** uit wat `next` zegt. Geen sprongen.
5. **Nieuw:** doe Fase 0 (intake) hieronder via `init` — niet handmatig alleen `state.md` knippen.
6. Toon Edwin de statustabel (zie hieronder) zodat hij in één oogopslag ziet waar de
   post staat — met name bij het hervatten van een lopende post.

### Statustabel — altijd tonen, nooit zelf opstellen

```bash
python3 scripts/orchestrate.py table --post <slug>
```

Print deze markdown-tabel **letterlijk** aan Edwin: bij het starten/hervatten van deze
skill, en na elke `complete`/`approve`/`reject` naast de samenvatting bij de gate. De
tabel is volledig **afgeleid** uit `state.json` + de bestanden op schijf (dezelfde
probe als `doctor`) — er wordt niets apart bijgehouden. Dat is bewust: een los
bijgehouden tabel is precies wat `state.md` liet driften vóór deze CLI er was. Bij
meerdere lopende posts (bijvoorbeeld tijdens intake van een nieuw deel terwijl een
vorig deel nog bij de deploy-gate staat) roep je `table` per slug aan; er is geen
overzicht over meerdere posts heen in v1.

### Standaardlus per content-fase

```text
next → (indien action=run) run <phase> → agent_brief uitvoeren → complete <phase>
     → (indien waiting_gate) samenvatten + Edwin vragen → approve of reject
     → herhaal
```

| CLI | Wanneer |
|-----|---------|
| `run <phase>` | Start van outline, draft, style, series, critique, synthesis, visuals, deploy |
| `complete <phase>` | Zodra het artefact er ligt (na agent/script) |
| `approve --note "..."` | Edwin akkoord bij gate |
| `reject --note "..."` | Opnieuw dezelfde phase |
| `set-flag yolo_mode true\|false` | Yolo aan/uit |
| `set-flag skip_synthesis\|defer_critique\|skip_factcheck true\|false` | Named exceptions (nooit stil overslaan) |
| `approve --deploy` | Zet `deploy_approved` vóór `run deploy` |
| `complete deploy --post-id N --edit-url URL` | Na geslaagde `deploy_post.py` |

Exitcode **2** = illegale stap of pre/post gefaald. Niet omzeilen: fix artefact of flag, of vraag Edwin.

`state.md` mag je bijwerken als **beslislog / reeks-context** (menselijk).  
**Fase en status** lees je niet uit `state.md` als `state.json` bestaat.

### Yolo

- Zetten: `set-flag yolo_mode true` (of `init --yolo`).
- Soft gates (outline, draft, style, series, critique, visuals): na `complete` kan de CLI
  zelf door naar de volgende phase (`yolo_advanced` in de output).
- Hard: **synthesis**-keuzes, **factcheck** en **deploy** — altijd stoppen, ook in yolo.
- Deploy-run vereist altijd `deploy_approved` (via `approve --deploy`).

## Huisstijl

Eén plek: `reference/huisstijl.md`. Niet dupliceren. Kern: feitelijk, sober, geen
gedachtestreep in lopende tekst (bullet lead-in mag), geen superlatieven, korte zinnen,
bron bij scherpe claims. Externe naden: `reference/externe-bronnen.md`.

## Fase 0 — Intake (nieuwe post)

1. Vraag het onderwerp. Geen onderwerp: backlog `backlog-blogpost-onderwerpen.md`
   (zie `reference/externe-bronnen.md`).
2. Bepaal kebab-case `slug` en werktitel. Bevestig met Edwin (**gate**).
3. Maak state aan **via de CLI**, niet door alleen het markdown-template te kopiëren:

   ```bash
   python3 scripts/orchestrate.py init --slug <slug> --titel "<werktitel>"
   # optioneel: --yolo
   # optioneel: --wait-intake-gate  (dan eerst approve vóór outline)
   ```

4. Optioneel: schrijf `posts/<slug>/state.md` als leesbaar logboek (reeks-context,
   brainstorm-verwijzing). Dit is **geen** vervanging van `state.json`.
5. Daarna: `next --post <slug>` → meestal `run outline`.

## Fasen 1–6 — content (via CLI + subagent)

Gebruik de **agent_brief** uit `run` / `next`. Korte mapping:

| phase (CLI) | Subagent | Artefact / resultaat |
|-------------|----------|----------------------|
| `outline` | `blogpost-onderzoeker` | `outline.md` |
| `draft` | `blogpost-schrijver` | `draft.md` |
| `style` | `stijl-check` **en** `leesbaarheid-check` | twee rapporten; draft eventueel corrigeren na gate |
| `series` | `reeks-consistentie-check` | rapport; draft corrigeren na gate |
| `critique` | `grok-reviewer` | `grok-feedback.md` (nooit verzonnen kritiek) |
| `synthesis` | `blogpost-onderzoeker` | `synthese.md`; Edwin beslist per punt; jij past `draft.md` aan na approve |
| `visuals` | `blogpost-visuals` | `visuals/*` + refs in draft; render via `scripts/render_svg.py` |
| `factcheck` | `bron-check` | `feitencheck.md`; **harde gate**, ook in yolo |
| `deploy` | `blogpost-deploy` | `scripts/deploy_post.py` → concept; daarna `complete deploy --post-id … --edit-url …` |

### Details die je niet mag vergeten

- **Schrijver:** leest outline + `reference/huisstijl.md`; verzint geen feiten buiten de outline.
- **Archief eerst.** Bij `outline`, `series` en `synthesis` begint de fase met
  `python3 scripts/rag_cli.py search "<onderwerp>" --top-k 12`, en met
  `reference/corpus-inventaris.md` ernaast. De `agent_brief` zet die stap er zelf in.
  Retrieval is lexicaal, dus varieer je zoektermen; een idee in andere woorden vindt de
  index niet, de inventaris wel. `reeks-consistentie-check` heeft geen Bash: draai de
  zoekopdracht zelf en geef de treffers mee.
- **Stijl-check / reeks-check:** rapporteren alleen; jij past draft aan na Edwins akkoord.
- **Leesbaarheid-check draait altijd naast de stijl-check**, in dezelfde fase, direct erna.
  De stijl-check telt uitsluitend overtredingen; onder die meetlat is de optimale tekst kort,
  onverbonden en voorzichtig. Bij deel 1 van de intentie-reeks leverde een correctieronde
  precies dat op: 14,7 woorden per zin tegen 16 tot 20 in de gepubliceerde reeks. De twee
  rapporten mogen elkaar tegenspreken; leg ze beide aan Edwin voor. Los een conflict nooit
  op door een feitelijkheidsregel te laten vallen, maar door te herschrijven.
- **Patch niet wat je moet herschrijven.** Meer dan vijf bevindingen in één sectie betekent:
  die sectie opnieuw schrijven. Losse ingrepen stapelen tot houterigheid, doordat elke
  splitsing een voegwoord weghaalt en elke schrapping een scharnier.
- **Reeks-check:** eerdere delen in `posts/*/`; bij eerste deel van een reeks mag het rapport leeg zijn.
- **Grok:** MCP `grok` + key in `.env`. Faalt de tool → `complete` niet forceren met nep-feedback; status blocked of reject, Edwin herstelt MCP.
- **Synthese:** hard gate. Geen stille skip — alleen `set-flag skip_synthesis true` als Edwin dat wil.
- **Herkeuring na de synthese (verplicht, beide checks).** De checks in fase 2b draaien op
  de draft zoals de schrijver hem opleverde. Daarna wijzig jij de draft nog bij de synthese
  en soms bij de visuals. Die wijzigingen zijn ongecontroleerd, en in de praktijk komen
  daar problemen uit: bij deel 1 van de intentie-reeks kwamen vijf van de zwaarste
  stijlbevindingen uit tekst die ná 2b was toegevoegd, en de leesbaarheid zakte onder de
  band juist doordat ik na de synthese zin voor zin patchte. **Roep daarom `stijl-check`
  én `leesbaarheid-check` opnieuw aan zodra je klaar bent met de draft-aanpassingen, vóór
  je `run deploy` doet.** Geef mee welke passages nieuw of gewijzigd zijn. Er is geen
  aparte CLI-fase voor; het zijn extra aanroepen binnen de bestaande fase.
- **Bron-check (fase 5b, `factcheck`) is de laatste controle vóór publicatie.** Hij legt elk
  citaat en elke bron naast de bron zelf, met `scripts/haal_bron.py` (dat ook PDF's leesbaar
  maakt). Dit is een **harde gate**: ook in yolo stopt de keten hier. `run deploy` weigert
  zolang `feitencheck.md` ontbreekt.
  Aanleiding: deel 1 van de intentie-reeks stond live met een citaat dat in de aangehaalde
  paper niet voorkomt. Dat kwam langs de schrijver, de stijl-check, de reeks-check, Grok en
  de synthese, omdat geen van die controles naar de bron kijkt. Overslaan kan alleen
  expliciet met `set-flag skip_factcheck true`; nooit stilzwijgend.
- **Visuals vóór critique:** alleen met `set-flag defer_critique true`.
- **Deploy:** nooit live. Script forceert `status: draft`. Eerst `approve --deploy`, dan run/complete.

## Wat deze skill niet doet

- Geen live publicatie.
- Geen fase verzinnen of overslaan zonder CLI-flag.
- Geen deploy/upload simuleren: echt `deploy_post.py` / `render_svg.py`, of niet.
- Geen `state.md`-tabel als waarheid zodra `state.json` bestaat.
