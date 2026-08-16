# ADR-006: Local RAG Archive Vectorstore for Archival Consistency

* **Status**: Accepted
* **Datum**: 2026-08-13
* **Laatst bijgewerkt**: 2026-08-16
* **Auteurs**: Edwin van Dillen

---

## 1. Context & Probleemstelling

Op `edwinvandillen.nl` en de bijbehorende reeksen (*Augmented Software Engineering*, *Intentie-gedreven Engineering*, *Token FinOps*, etc.) worden complexe IT- en AI-thema's in een doorlopende rode draad behandeld. 

Naarmate het archief groeit, wordt het voor de `blogpost-onderzoeker` en `blogpost-schrijver` lastiger om uit het hoofd te weten welke definities, denkkaders, metaforen en eerdere conclusies al eerder zijn vastgelegd. Zonder geautomatiseerd geheugen ontstaat het risico dat begrippen inconsistent worden gebruikt, of dat eerdere artikelen niet scherp worden aangehaald.

---

## 2. Overwogen Alternatieven

1. **Eerdere Posts Handmatig Inlezen via WordPress REST API**: De onderzoeker haalt bij elke run de laatste 10 posts op via de live site (`per_page=10`).
   - *Nadeel*: Beperkt tot recente posts, mist diepe semantische doorzoekbaarheid, traag en afhankelijk van netwerk.
2. **Volledige Archief-Markdown Bestanden in Prompt Invoegen**: Alle historische posts meegeven in het context-window van de LLM.
   - *Nadeel*: Context-window vervuiling, hoge tokenkosten en verminderde focus van het model.
3. **Lokale RAG Archiefindex van de live site (Gekozen)**: Alleen wat op `edwinvandillen.nl` live staat, ophalen via de WordPress REST API en lokaal indexeren.
4. **Lokale werkmappen meenemen (`draft.md`, `outline.md`, …)** — eerder gedaan, **verworpen op 2026-08-16**.
   - *Nadeel*: de index bevat dan werk in uitvoering. Deel 3 van de intentie-reeks stond in de RAG terwijl het artikel niet live was. De onderzoeker en de alignment-check lazen daardoor een onafgemaakte outline als “wat we eerder zeiden”.

---

## 3. Beslissing

We bouwen een **lokale RAG (Retrieval-Augmented Generation) Archiefindex**:

- **Bron van waarheid is de live site.** Alleen wat op **https://edwinvandillen.nl** als gepubliceerde post staat, mag in de RAG. De indexer haalt altijd op vanaf die site, via de WordPress REST API (`?rest_route=/wp/v2/posts&status=publish`). Nooit vanuit `posts/<slug>/`.
- **Niet indexeren:** lokale `draft.md`, `outline.md`, `synthese.md`, `briefing.md`, WordPress-concepten, en mappen van posts die nog niet live staan. Die bestanden zijn werk in uitvoering, geen archief.
- **Indexering**: de opgehaalde live HTML wordt ge-chunked per alinea en opgeslagen in één JSON-index op schijf (`posts/.archive_rag_index.json`). Retrieval blijft lokaal; alleen het vullen van de index praat met de site.
- **Retrieval**: **TF-IDF met cosine-gelijkenis** over unigrammen en bigrammen. Geen embeddings en geen vector-database. Dat is een bewuste beperking: het vindt letterlijke termen en woordparen betrouwbaar, maar niet een eerder geformuleerd idee in heel andere woorden. Zie de bijwerking hieronder.
- **Consumptie door `blogpost-onderzoeker` (Fase 1)**: De onderzoeker befragt de vectorstore tijdens de brainstorm/outline-fase om gerichte verwijzingen, frameworks en definities uit het verleden op te halen.
- **Consumptie door `blogpost-schrijver` (Fase 2)**: De schrijver gebruikt de RAG-context om de authentieke stem, specifieke terminologie en opgebouwde argumentatie naadloos voort te zetten.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**:
  - Gegarandeerde inhoudelijke en terminologische continuïteit over meerdere reeksen heen.
  - Gerichte zoekopdrachten op terminologie zonder tokens te verspillen.
  - Werkt 100% lokaal en offline op de eigen computer; geen model-aanroep bij retrieval.
* **Negatief (-)**:
  - (Her)indexeren vereist netwerk naar edwinvandillen.nl. Zoeken zelf blijft lokaal.
  - Een lokale herschrijving van een al live post verschijnt pas in de RAG nadat die tekst live staat.
  - Lexicaal zoeken vindt "stroomopwaarts" wel, maar "de controle naar voren halen" niet. `reference/corpus-inventaris.md` is het vangnet daaronder.

---

## 5. Bijwerking 2026-08-14

De oorspronkelijke tekst sprak van "een lokale vector-database met embeddings" en van
"semantische doorzoekbaarheid". De implementatie was en is TF-IDF; embeddings zijn nooit
gebouwd. Ontwerp en implementatie zijn nu gelijkgetrokken op wat er staat: lexicaal zoeken.

Tegelijk is de retrieval gerepareerd (zie `docs/plan-kwaliteitsverbetering-workflow.md`, blok A):

- IDF-weging toegevoegd; daarvoor woog elke term even zwaar, waardoor stopwoorden en
  algemene vaktermen de ranglijst bepaalden.
- Incrementeel indexeren vergelijkt per live artikel op de WordPress-`modified`-tijd.
  Een herschreven *live* post wordt opnieuw opgehaald. Een lokale draft telt niet.
- Een bron wordt in zijn geheel vervangen, niet chunk voor chunk aangevuld, en verdwenen
  live artikelen worden uit de index verwijderd.

Alsnog embeddings bouwen blijft een open optie. Die keuze vraagt een nieuwe ADR, want ze
brengt een modelaanroep of een lokaal embeddingmodel de keten in.

---

## 6. Bijwerking 2026-08-16 — alleen live, altijd vanaf de site

Aanleiding: in de index stonden naast de WordPress-kopieën van deel 1 en 2 ook de
lokale mappen `intentie-1-…`, `intentie-2-…` en `intentie-3-…`. Deel 3 bestond
nog niet live. De RAG bevatte dus een outline in wording als ware het archief.

**Besluit, bindend voor de implementatie:**

1. **`edwinvandillen.nl` is de enige bron van waarheid** voor wat “eerder
   geschreven” is. Niet `posts/`, niet `state.json`, niet een concept in wp-admin.
2. **Alleen status `publish`.** Concepten, privéberichten en revisions horen niet
   in de index. De fetch zet `status=publish` expliciet.
3. **Altijd ophalen vanaf de site.** Elke (her)index-run praat met
   `https://edwinvandillen.nl/?rest_route=/wp/v2/posts`. Er is geen pad dat
   lokale markdown in de index schrijft.
4. **Bestaande `local:`-chunks verdwijnen** bij de eerstvolgende index-run.
   Zo blijft een oude index niet stiekem werk-in-uitvoering serveren.
5. **Zoeken herindexeert niet vanuit `posts/`.** Een zoekopdracht leest de
   laatst opgehaalde live index. Vernieuwen hoort bij de Settings-actie
   “herindexeren”, die opnieuw van de site haalt.

De vorige zin in §3 die lokale artefacten meenam, is hiermee ingetrokken.
