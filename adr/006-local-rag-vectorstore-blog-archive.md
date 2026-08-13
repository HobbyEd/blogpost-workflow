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
3. **Lokale RAG Vectorstore Index (Gekozen)**: Alle reeds geschreven en gepubliceerde blogposts indexeren in een lokale vector-database met embeddings.

---

## 3. Beslissing

We bouwen een **lokale RAG (Retrieval-Augmented Generation) Archief Vectorstore**:

- **Indexering**: Alle gepubliceerde blogposts en reeksen worden ge-chunked en ge-indexeerd in een lokale vectorstore (bijv. ChromaDB of LanceDB met embeddings).
- **Consumptie door `blogpost-onderzoeker` (Fase 1)**: De onderzoeker befragt de vectorstore tijdens de brainstorm/outline-fase om gerichte verwijzingen, frameworks en definities uit het verleden op te halen.
- **Consumptie door `blogpost-schrijver` (Fase 2)**: De schrijver gebruikt de RAG-context om de authentieke stem, specifieke terminologie en opgebouwde argumentatie naadloos voort te zetten.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**:
  - Gegarandeerde inhoudelijke en terminologische continuïteit over meerdere reeksen heen.
  - Slimme semantische zoekmogelijkheden zonder tokens te verspillen.
  - Werkt 100% lokaal en offline op de eigen computer.
* **Negatief (-)**:
  - Vereist een geautomatiseerd synchronisatiescript om nieuwe gepubliceerde posts direct aan de RAG-index toe te voegen.
