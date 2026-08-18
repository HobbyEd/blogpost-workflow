# ADR-011: Verbruiksbalk — Claude-limieten en Grok-saldo in de UI

* **Status**: Accepted
* **Datum**: 2026-08-18
* **Auteurs**: Edwin van Dillen
* **Gerelateerd**: [ADR-001 (Strikte control plane)](001-strict-deterministic-control-plane.md), [ADR-008 (Settings & RAG)](008-admin-settings-tab-and-background-rag-indexer.md)

---

## 1. Context & Probleemstelling

De keten verbrandt Claude-abonnementslimiet (worker via `claude -p`) en, in de
kritiekfase, prepaid Grok-credits (MCP `grok_review`). Die twee meters zaten
nergens in het Command Center. Wie wilde weten of de 5-uurslimiet eraan kwam,
moest `/usage` in Claude Code openen. Wie wilde weten of Grok nog saldo had,
moest de xAI-console openen.

Op 18 augustus zat de 5-uursmeter op 84% gebruikt terwijl een post op stijl
wachtte. Dat is precies het moment waarop je wilt zien of de volgende run
nog past, zonder van scherm te wisselen.

Twee vragen lagen onder die wens:

1. Waar haal je de cijfers vandaan, zonder een tweede factuur of een
   periodieke poll die zelf tokens kost?
2. Mag de Grok-MCP-server het saldo leveren, of is dat een ander kanaal?

Dit is geen gate-besluit (ADR-010) en geen RAG-beheer (ADR-008). Het is een
observatievlak over de twee providers waarop de execution plane draait.

---

## 2. Overwogen Alternatieven

### Alternatief A: niets in de UI, blijf `/usage` en de console gebruiken

Geen code, geen extra credentials. Nadeel: de auteur ziet de meter pas als hij
er al tegenaan loopt, en nooit in dezelfde blik als de stepper.

### Alternatief B: periodiek pollen (elke minuut) vanuit de UI

De balk blijft vanzelf actueel. Nadeel: de Claude-usage-API wordt tientallen
keren per uur geraakt terwijl er niets gebeurt, en het cijfer verandert alleen
als er een run is geweest. Op 18 augustus was dat de eerste implementatie; die
is dezelfde dag teruggedraaid.

### Alternatief C: balk rechts, cijfers ophalen bij openen en ná een activiteit

Zelfde bronnen als B, maar de UI vraagt opnieuw als er iets is gebeurd dat
tokens of credits kán hebben gekost: een worker-run die klaar is, of een
gate-actie. Handmatig verversen blijft mogelijk.

---

## 3. Beslissing

**C.** Rechts van het Command Center staat een verbruiksbalk. Die hoort bij
alle drie de modi, niet alleen bij de stepper.

### 3.1 Wat de balk toont

| Meter | Cijfer | Reset |
|---|---|---|
| Claude 5-uur venster | percentage *vrij* (100 minus `utilization`) | lokale tijd van `resets_at` |
| Claude weekbudget | percentage *vrij* | lokale datum en tijd van `resets_at` |
| Grok prepaid | resterende dollars, of waarom ze ontbreken | geen reset; het is een saldo |

Het Claude-venster is **vijf uur**, niet zes. Zo meet Anthropic het; `/usage`
in Claude Code toont hetzelfde. De balk noemt het daarom "5-uur venster".

### 3.2 Bronnen

**Claude.** Dezelfde OAuth-login als Claude Code, uit de macOS-sleutelhanger
(`Claude Code-credentials`). `GET https://api.anthropic.com/api/oauth/usage`
levert `five_hour` en `seven_day`. Het access-token wordt alleen ververst als
het verlopen is of de usage-call 401 geeft; een geldig token wordt niet
proactief geroteerd, omdat Claude Code dezelfde refresh-token gebruikt.

Dit is geen tweede Anthropic-rekening en geen API-key. Het is het
abonnement dat de worker al gebruikt.

**Grok.** De bestaande MCP-server (`.claude/mcp/grok_review_server.py`) biedt
`grok_review` en, sinds deze ADR, `grok_credits`. Die tweede tool leest
**niet** uit de inference-key. `GROK_API_KEY` mag `/v1/api-key` (team-id)
zien, maar de Management API (`GET /v1/billing/teams/{id}/prepaid/balance`)
weigert hem met "use a valid management key".

Het saldo verschijnt pas als `XAI_MANAGEMENT_KEY` in `.env` staat (aanmaken:
console.x.ai → Settings → Management Keys). Zonder die key zegt de balk
waarom het cijfer ontbreekt, in plaats van een nulfout.

De web-UI praat niet met MCP. Beide vlakken (UI en `grok_credits`) roepen
dezelfde functie aan: `scripts/orchestrator/provider_usage.py`. MCP blijft
stdio voor Claude; het Command Center blijft FastAPI.

### 3.3 Wanneer de balk ververst

| Moment | Wat er gebeurt |
|---|---|
| Pagina openen | één keer `GET /api/usage` |
| Worker-run klaar (`running` → iets anders) | `GET /api/usage?fresh=1` |
| Gate-actie (goedkeuren, afwijzen, afronden, toch verder) | `GET /api/usage?fresh=1` |
| Klik op ↻ | `GET /api/usage?fresh=1` |
| Elke N seconden | **niet** |

`fresh=1` slaat de 45-seconden-cache over. Zonder die parameter zou een
net afgeronde run het cijfer van vóór de run kunnen tonen.

Een `run` die nét start, ververst de balk niet. De tokens zijn dan nog niet
uitgegeven; dat gebeurt als de worker klaar is.

### 3.4 Wat hier niet in zit

- Geen schatting "past deze fase nog in het venster". De balk toont de
  meter, niet een voorspelling.
- Geen Grok-saldo zonder management key. Dat is een bewuste weigering, geen
  ontbrekend stukje parser.
- Geen schrijven van verbruik naar `state.json`. Dit is observatie, geen
  control-plane-feit.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**
  - De auteur ziet de twee meters naast de stepper, op het moment dat hij
    besluit of hij een run start.
  - Claude-cijfers komen uit de login die er al is; geen extra abonnement.
  - De balk belast de usage-API niet terwijl er niets gebeurt.
* **Negatief (-)**
  - Grok-saldo vraagt een tweede secret (`XAI_MANAGEMENT_KEY`) naast
    `GROK_API_KEY`. Zonder die key is het Grok-blok een uitleg, geen cijfer.
  - Token-refresh schrijft terug naar de sleutelhanger. Twee processen die
    tegelijk verversen kunnen elkaars refresh-token ongeldig maken. Daarom
    alleen verversen bij verlopen of 401.
* **Risico's**
  - De usage-URL (`/api/oauth/usage`) is hetzelfde pad als Claude Code
    `/usage`, geen gedocumenteerde publieke API. Als Anthropic hem verplaatst,
    valt de balk zacht om (`ok: false` met reden), de keten niet.
  - De balk is geen garantie dat de volgende run past. Een stijl-check kan
    het restant van 16% alsnog opmaken.

---

## 5. Uitvoering

Uitgevoerd 2026-08-18.

- `scripts/orchestrator/provider_usage.py` — lezen, cachen, formatteren.
- `GET /api/usage` en `GET /api/usage?fresh=1` in `server.py`.
- Rechterbalk in `web/index.html` / `web/app_v2.js` / `web/styles.css` (v1.20).
- MCP-tool `grok_credits` in `.claude/mcp/grok_review_server.py`.
- `XAI_MANAGEMENT_KEY` in `.env_template` (leeg, geen geheim).
