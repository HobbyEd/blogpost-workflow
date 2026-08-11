# Externe bronnen — de enige koppeling naar buiten de repo

De workflow-code is zelfstandig. De huisstijl (`reference/huisstijl.md`) en de
deploy-procedure (`reference/deploy.md`) staan in de repo. Er blijven twee inputs die
**bewust** buiten de repo leven, want het is data van Edwin die los van deze code
verandert. Dit bestand is de enige plek waar hun locatie is vastgelegd. Verwijs vanuit
subagents en de skill hiernaar, niet naar een hardgecodeerd `../`-pad.

## 1. Postcorpus (voor context)

Edwins eerdere blogposts, als context voor de onderzoeker (fase 1). Het corpus komt
**van de live site edwinvandillen.nl** via de WordPress REST API, niet van een map op
schijf. Zo hangt de repo nergens aan een naburige map; er is alleen internettoegang
nodig.

- **Bron:** de gepubliceerde posts, nieuwste eerst:

  ```
  https://edwinvandillen.nl/?rest_route=/wp/v2/posts&per_page=10&orderby=date&order=desc&_fields=id,title,link,date,excerpt
  ```

  Dit geeft een compacte JSON-lijst (titel, link, datum, excerpt). Wil je de volledige
  tekst van een post voor toon of inhoud, voeg dan `content` toe aan `_fields` of haal
  de losse post-`link` op. Lezen van gepubliceerde posts vereist geen authenticatie.
- **Aantal:** standaard de laatste 10 (`per_page=10`). Meer of minder: pas `per_page`
  aan.
- **Afwezig / offline?** Kan de site niet worden bereikt, dan is dat geen fout: de
  contextstap levert een lege context en de post wordt zonder corpus-verankering
  geschreven. Meld dat bij de gate.
- **Toekomst (RAG):** dit is de "vervangbare contextophaling". Later wordt deze directe
  site-fetch één query op een kleine RAG-index over dezelfde posts. De in-/output van
  de contextstap blijft gelijk, zodat de omruil de rest van de keten niet raakt.

## 2. Backlog (voor de intake)

De ideeënlijst met blogpost-onderwerpen en hun intentie, gebruikt in fase 0 als Edwin
nog geen onderwerp heeft (of om de reeks-lijn te bewaken).

- **Locatie:** `backlog-blogpost-onderwerpen.md` in de repo-root. Anders dan het
  postcorpus staat dit bestand wél in de repo (het is workflow-/reeks-planning, geen
  postinhoud). Ontbreekt het, dan vraagt de intake het onderwerp gewoon uit.
- Vul de backlog aan zodra onderweg nieuwe ideeën ontstaan.

- `GROK_API_KEY`, `WP_APPLICATION_TOKEN`, `WP_SITE_URL` en `WP_USERNAME` staan in `.env` in de repo-root.
  `.env` is gitignored. De Grok-MCP-server en het deploy-script lezen ze daar.
