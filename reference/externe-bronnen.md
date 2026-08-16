# Externe bronnen — de enige koppeling naar buiten de repo

De workflow-code is zelfstandig. De huisstijl (`reference/huisstijl.md`) en de
deploy-procedure (`reference/deploy.md`) staan in de repo. Er blijven twee inputs die
**bewust** buiten de repo leven, want het is data van Edwin die los van deze code
verandert. Dit bestand is de enige plek waar hun locatie is vastgelegd. Verwijs vanuit
subagents en de skill hiernaar, niet naar een hardgecodeerd `../`-pad.

## 1. Postcorpus (voor context)

Edwins eerdere blogposts, als context voor de onderzoeker (fase 1) en de
reeks-consistentiecheck. Het corpus komt **van de live site edwinvandillen.nl** via de
WordPress REST API. Zo hangt de repo nergens aan een naburige map; er is alleen
internettoegang nodig.

Je bevraagt het corpus niet meer rechtstreeks per fetch, maar via de RAG-index:

- **Zoeken:** `python3 scripts/rag_cli.py search "<onderwerp>" --top-k 12`. De index dekt
  alleen live posts van edwinvandillen.nl (ADR-006). Retrieval is lexicaal
  (TF-IDF, geen embeddings): varieer je zoektermen, want een idee in andere woorden vindt
  hij niet.
- **Vangnet:** `reference/corpus-inventaris.md` — alle 61 posts met id, datum, titel en
  kernbegrippen. Loop die lijst door voor wat de zoekopdracht mist.
- **Bijwerken:** `python3 scripts/rag_cli.py reindex --incremental` haalt nieuwe en
  gewijzigde posts op. `--purge` bouwt de index van nul op. De index staat in
  `posts/.archive_rag_index.json` en is gitignored.
- **Volledige tekst van één post:** `https://edwinvandillen.nl/?p=<id>`, of de
  REST-route hieronder. Lezen van gepubliceerde posts vereist geen authenticatie.

  ```
  https://edwinvandillen.nl/?rest_route=/wp/v2/posts&per_page=10&orderby=date&order=desc&_fields=id,title,link,date,excerpt
  ```

  Let op: deze route geeft standaard alleen de nieuwste posts. Precies dat venster maakte
  ouder materiaal onzichtbaar; gebruik hem dus om één bekende post op te halen, niet om
  het archief te verkennen.
- **Afwezig / offline?** Kan de index niet worden gelezen of de site niet worden bereikt,
  dan is dat geen fout: werk verder met de corpus-inventaris en meld het bij de gate.
  Verzin geen eerdere posts.

## 2. Backlog (voor de intake)

De ideeënlijst met blogpost-onderwerpen en hun intentie, gebruikt in fase 0 als Edwin
nog geen onderwerp heeft (of om de reeks-lijn te bewaken).

- **Locatie:** `backlog-blogpost-onderwerpen.md` in de repo-root. Anders dan het
  postcorpus staat dit bestand wél in de repo (het is workflow-/reeks-planning, geen
  postinhoud). Ontbreekt het, dan vraagt de intake het onderwerp gewoon uit.
- Vul de backlog aan zodra onderweg nieuwe ideeën ontstaan.

- `GROK_API_KEY`, `WP_APPLICATION_TOKEN`, `WP_SITE_URL` en `WP_USERNAME` staan in `.env` in de repo-root.
  `.env` is gitignored. De Grok-MCP-server en het deploy-script lezen ze daar.
