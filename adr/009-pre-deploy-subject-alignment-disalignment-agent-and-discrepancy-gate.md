# ADR-009: Pre-Deploy Inhoudelijke Alignment/Disalignment Agent & Discrepantie Decision Gate

* **Status**: Accepted
* **Datum**: 2026-08-13
* **Auteurs**: Edwin van Dillen & Antigravity AI Team
* **Gerelateerd**: [ADR-004 (Hard vs Soft Gates)](004-hard-soft-quality-gates-strategy.md), [ADR-006 (Local RAG Vectorstore)](006-local-rag-vectorstore-blog-archive.md), [ADR-007 (Archival Alignment Agent)](007-archival-alignment-validation-agent.md)

---

## 1. Context & Probleemstelling

Bij het schrijven van blogposts over een langere periode ontstaan er twee reële risico's:
1. **Onbedoelde Inhoudelijke Inconsistentie (Fout)**: Een agent of auteur stelt per ongeluk iets dat haaks staat op een eerder gepubliceerd artikel op edwinvandillen.nl, zonder dat dit de bedoeling was.
2. **Intentionele Koerswijziging (Voortschrijdend Inzicht)**: De auteur heeft nieuwe inzichten opgedaan en stapt bewust af van een eerder ingenomen standpunt. Dit is inhoudelijk waardevol, mits de afwijking bewust is en transparant wordt afgewogen.

Het systeem moet vlak vóór publicatie (Pre-Deploy) automatisch detecteren of een artikel **Aligned** (in lijn) of **Disaligned / Discrepant** (afwijkend) is ten opzichte van het RAG-blogarchief, en de auteur in de Web UI een expliciete keuze voorschotelen.

---

## 2. Architectonisch Ontwerp & Workflow

De **Alignment/Disalignment Agent** wordt gepositioneerd als een **veiligheidspoort (Quality Gate)** direct voor de Deploy-fase.

```
 [Fase 5b: Factcheck] ➔ [Fase 5c: Archief Alignment Check] ➔ [Kwaliteits-Gate] ➔ [Fase 6: Deploy]
                                  |
                                  v
                        RAG Semantic Search
                                  |
                      +-----------+-----------+
                      |                       |
               [ALIGNMENT_OK]       [DISCREPANCY_DETECTED]
                      |                       |
            Automatisch Akkoord       Web UI Waarschuwing & Decision Gate
                                              |
                                   +----------+----------+
                                   |                     |
                        [Voortschrijdend Inzicht] [Inhoudelijke Fout]
                                   |                     |
                         Accepteer met Notitie     Zet terug naar Draft
                                   |                     |
                           Door naar Deploy         Herstel Concept
```

---

## 3. Functionele Specificaties

### A. Automatische Analyse & Classificatie
De agent analyseert het concept (`draft.md` / `synthese.md`) aan de hand van de RAG vectorstore:
1. **Semantische Vergelijking**: De kernstellingen, begrippen en conclusies worden vergeleken met eerdere artikelen in het RAG-archief.
2. **Resultaat Classificatie**:
   - **`ALIGNMENT_OK`**: De inhoud sluit naadloos aan bij eerdere publicaties.
   - **`DISCREPANCY_DETECTED`**: Er is een inhoudelijke afwijking, tegenstrijdige bewering of gewijzigde definitie gevonden.

---

### B. Web UI Interactie & Discrepantie Decision Gate
Wanneer een afwijking (`DISCREPANCY_DETECTED`) wordt geconstateerd, gebeurt het volgende in de Web UI:

1. **Visuele Statusmelding**:
   - Op de Stepper (Modus 2) krijgt de fase een oranje/amber status met de badge:  
     `⚠️ Inhoudelijke Discrepantie Gevonden`.
2. **Discrepantie Rapport Inzien**:
   - In het viewer-paneel verschijnt de vergelijking met het eerdere artikel, inclusief de exacte citaten en de geconstateerde afwijking.
3. **Expliciete Keuzeopties voor de Auteur**:
   In de Web UI worden twee knoppen gepresenteerd:

   * **Optie A: "💡 Accepteer als Voortschrijdend Inzicht" (Intentionele Afwijking)**:
     - De auteur geeft aan dat de afwijking bewust en correct is.
     - Er verschijnt een verplicht notitieveld waarin de auteur de reden toelicht (bijv. *"Voortschrijdend inzicht: We stappen af van monolithische modellen naar gedistribueerde agents"*).
     - De notitie wordt opgeslagen in `state.json` en het rapport `archief-consistentie.md`.
     - De kwaliteits-gate schakelt over naar **Groen (Ready for Deploy)**.

   * **Optie B: "❌ Afwijzen als Inhoudelijke Fout" (Onbedoelde Discrepantie)**:
     - De auteur stelt vast dat er een fout of verkeerde formulering in de blogpost zit.
     - De kwaliteits-gate wordt afgekeurd en de post status gaat terug naar `ready` in de fase `draft` of `synthesis`.
     - Het rapport met de tegenstrijdigheid blijft behouden als feedback voor de schrijver-agent om het concept te herstellen.

---

## 4. REST API & Data Model

### A. State.json Uitbreiding
```json
{
  "archival_alignment": {
    "status": "DISCREPANCY_DETECTED",
    "score": 0.65,
    "discrepancies": [
      {
        "historical_slug": "intentie-1-introductie",
        "topic": "Agent architectuur",
        "previous_stance": "Gebruik één centraal model",
        "current_stance": "Gebruik meerdere gedecentraliseerde subagents"
      }
    ],
    "resolution": {
      "type": "progressive_insight",
      "author_note": "Voortschrijdend inzicht t.o.v. deel 1",
      "resolved_at": "2026-08-13T18:50:00Z"
    }
  }
}
```

### B. REST Endpoints
- `POST /api/posts/{slug}/alignment-check`: Triggert de Alignment/Disalignment analyse.
- `POST /api/posts/{slug}/resolve-discrepancy`:
  Request Body:
  ```json
  {
    "resolution_type": "progressive_insight | error_rejected",
    "note": "Toelichting van de auteur bij voortschrijdend inzicht"
  }
  ```

---

## 5. Reflectie op Volledigheid & Kwaliteit

### Is deze ADR compleet genoeg?

| Criterium | Status | Toelichting |
|---|---|---|
| **Sectie-Indeling & Duidelijkheid** | ✅ **100% Compleet** | Vaste ADR-structuur met heldere context, besluit, diagram en uitgewerkte UI-keuzes. |
| **Snelheids- & Workflow Veiligheid** | ✅ **100% Compleet** | Zorgt dat een inhoudelijke afwijking nooit stilzwijgend door de YOLO-modus glipt; een menselijke beslissing is verplicht bij afwijkingen. |
| **Onderscheid Fout vs. Inzicht** | ✅ **100% Compleet** | Ondersteunt expliciet zowel de 'Fout herstellen'-flow als de 'Voortschrijdend inzicht'-flow. |
| **Auditbaarheid & Historie** | ✅ **100% Compleet** | Toelichtingsnotities bij voortschrijdend inzicht worden vastgelegd in `state.json` en de logs, zodat de evolutie van inzichten later te herleiden is. |

---

## 6. Consequenties (Consequences)

### Positief:
- **Maximale Inhoudelijke Bewaking**: Voorkomt ongemerkte tegenstrijdigheden met het bestaande oeuvre.
- **Vrijheid voor Innovatie**: Biedt een soepele, gestructureerde manier om voortschrijdende inzichten te documenteren zonder de pipeline te blokkeren.
- **Heldere UI/UX**: De auteur ziet in één oogopslag wát er afwijkt en kan direct de juiste actie kiezen.

### Aandachtspunten voor Implementatie:
- De Alignment Agent moet scherp genoeg gebouwd worden dat stijlverschillen niet ten onrechte als inhoudelijke contradictie worden aangemerkt.
