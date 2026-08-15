# ADR-006: Local RAG Archive Vectorstore for Archival Consistency

* **Status**: Proposed
* **Datum**: 2026-08-13
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
3. **Lokale RAG Archiefindex (Gekozen)**: Alle reeds geschreven en gepubliceerde blogposts indexeren in een lokale index op de eigen schijf.

---

## 3. Beslissing

We bouwen een **lokale RAG (Retrieval-Augmented Generation) Archiefindex**:

- **Indexering**: Alle gepubliceerde blogposts en reeksen, plus de lokale artefacten (`draft.md`, `synthese.md`, `outline.md`, `briefing.md`), worden ge-chunked per alinea en ge-indexeerd in één JSON-index op schijf (`posts/.archive_rag_index.json`).
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
  - Vereist een geautomatiseerd synchronisatiescript om nieuwe gepubliceerde posts direct aan de RAG-index toe te voegen.
  - Lexicaal zoeken vindt "stroomopwaarts" wel, maar "de controle naar voren halen" niet. `reference/corpus-inventaris.md` is het vangnet daaronder.

---

## 5. Bijwerking 2026-08-14

De oorspronkelijke tekst sprak van "een lokale vector-database met embeddings" en van
"semantische doorzoekbaarheid". De implementatie was en is TF-IDF; embeddings zijn nooit
gebouwd. Ontwerp en implementatie zijn nu gelijkgetrokken op wat er staat: lexicaal zoeken.

Tegelijk is de retrieval gerepareerd (zie `plan-kwaliteitsverbetering-workflow.md`, blok A):

- IDF-weging toegevoegd; daarvoor woog elke term even zwaar, waardoor stopwoorden en
  algemene vaktermen de ranglijst bepaalden.
- Incrementeel indexeren vergelijkt nu per bestand op mtime in plaats van per postmap over te
  slaan; een herschreven draft wordt dus opnieuw geïndexeerd.
- Een bron wordt in zijn geheel vervangen, niet chunk voor chunk aangevuld, en verdwenen
  bronnen worden uit de index verwijderd.

Alsnog embeddings bouwen blijft een open optie. Die keuze vraagt een nieuwe ADR, want ze
brengt een modelaanroep of een lokaal embeddingmodel de keten in.
