# Ontwerpdocument: Blogpost Workflow Web UI & Agent Platform

*Architectuur-, uitgangspunten- en faseringsdocument voor de ontwikkeling van een web-gebaseerd Redactioneel Command Center op basis van de Blogpost Agentic Workflow.*

---

## 1. Visie & Doelstelling

De **Blogpost Workflow** is in de v1-fase succesvol ingericht als een deterministische Python CLI (`scripts/orchestrate.py`) gecombineerd met LLM-subagents. Dit borgt dat de status en transitielogica onafhankelijk van de LLM-prompt verlopen. 

Het doel van dit ontwerp is de evolutie van een terminal-gebaseerde CLI naar een **volwaardige Web UI**. Deze interface transformeert de workflow van een mechanisch commandoregel-proces naar een **interactief redactioneel Command Center** waarin menselijke creativiteit, socratische AI-co-creatie en geautomatiseerde agent-executie naadloos samenkomen.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Blogpost Command Center Web UI                       │
├───────────────────────────────────┬────────────────────────────────────┤
│ 💡 Modus 1: Interactiviteit       │ 🚀 Modus 2: Executie Engine        │
│ • Socratische brainstorm met AI   │ • YOLO / Stepper Agent Keten       │
│ • Reeks- & Themaverkenning        │ • Visuele Bolletjesketen (Status)  │
│ • Genereert Uitgangspuntendocument│ • Automatisering t/m Concept Deploy│
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 2. Kernfunctionaliteiten & Gebruikerservaring

### 2.1 Modus 1: Interactieve Brainstorm & Co-Creatie (De Onderzoeker)
Voorafgaand aan het starten van de geautomatiseerde schrijfketen bevindt de gebruiker zich in de **Interactieve Modus**:
- **Socratische Dialoog**: De gebruiker werkt synchroon samen met de `blogpost-onderzoeker` agent. De AI stelt verhelderende vragen over het doel, de beoogde lezers, de invalshoek en de gewenste thesis.
- **Enkelvoudige Post vs. Reeks**: In deze modus wordt vastgesteld of het onderwerp leent voor één losstaand artikel of een meerdelige artikelenreeks (bijv. de *Intentie-reeks* of *Anatomie van Agents-reeks*).
- **Output — Het Uitgangspuntendocument**: De interactieve sessie resulteert in een gestructureerd **Uitgangspuntendocument** (`briefing.md` / `ontwerp.md`). Dit document bevat de kernhypothese, de hoofdlijnen, de gewenste toon en de afbakening die als input dient voor Fase 0/1 van de executieketen.

### 2.2 Modus 2: YOLO Executie & De Visuele Bolletjesketen
Zodra de uitgangspunten vaststaan, kan de gebruiker met één klik de **YOLO-modus** activeren voor een specifieke post.

- **De Visuele Bolletjesketen (Stepper)**:
  De UI toont een overzichtelijke keten van status-bolletjes die in reële tijd de voortgang van de subagents weerspiegelen:

```
 (0) ──────> (1) ──────> (2) ──────> (2b) ──────> (2c) ──────> (3) ──────> [4] ──────> (5) ──────> [5b] ──────> ★ ──────> [6]
Intake     Outline     Draft       Stijl       Reeks     Critique    Synthese   Visuals   Factcheck   Herkeur    Deploy
 🟢          🟢          🟢          🟢          🟢          🟢         🔴         ⚪         ⚪         ⚪         ⚪
```

- **Kleurcodes & Status-indicatoren**:
  - ⚪ **Grijs (Pending)**: Fase is nog niet gestart.
  - 🔵 **Pulserend Blauw (Running)**: Subagent of script is momenteel actief.
  - 🟢 **Groen (Completed)**: Fase is succesvol afgerond en artefact is aanwezig op schijf.
  - 🟡 **Oranje/Amber (Waiting Gate)**: Wacht op menselijk akkoord (soft of hard gate).
  - 🔴 **Rood (Hard Gate / Blocked)**: Stopt verplicht voor menselijke goedkeuring (Fase 4 Synthese, Fase 5b Factcheck, Fase 6 Deploy) of een geblokkeerde fout.

### 2.3 Menselijke Vrijgave & WordPress Concept Deploy
- **Geen Automatische Live Publicatie**: Wanneer de gehele agent-keten is doorlopen, omgezet naar Gutenberg-blokken en geüpload naar WordPress via `deploy_post.py`, krijgt de post de status **`draft` (concept)**.
- **Handmatige Eindcontrole**: De Web UI presenteert direct de WordPress `edit_url` en het concept-ID. De auteur opent wp-admin en voert de finale publicatie handmatig uit.

---

## 3. Systeemarchitectuur & Componenten

De Web UI wordt gebouwd op een ontkoppelde 3-laags architectuur:

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Frontend (React / Web UI)                          │
│   • Redactioneel Dashboard    • Socratische Chat (Interactie)          │
│   • Stepper / Bolletjesketen  • Live Markdown & Visual Viewer          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTP REST / WebSockets (SSE)
┌──────────────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Web Backend (Python)                        │
│   • REST Endpoints (/api/posts)  • Async Task Runner (Subagents)       │
│   • WebSocket Stream (Logs)      • Chat Session Manager                │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Pure Python API
┌──────────────────────────────────▼─────────────────────────────────────┐
│                 Orchestrator Package (`orchestrator/`)                 │
│   • Service Layer                • State Machine Engine                │
│   • Probes & File Repositories   • CLI Wrapper (`orchestrate.py`)      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Reads/Writes
┌──────────────────────────────────▼─────────────────────────────────────┐
│                  Lokale Schijf (`posts/[slug]/state.json`)             │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Refactoring van `scripts/orchestrate.py` naar `orchestrator/` Package
Om de CLI en de Web UI exact dezelfde bedrijfslogica te laten delen, wordt de huidige 1.600+ regels grote `orchestrate.py` opgesplitst in een modulair Python package:

```text
scripts/
├── orchestrate.py                # Dunne CLI wrapper (voor terminal gebruik)
└── orchestrator/                 # Python package
    ├── constants.py              # PHASES, GATES, FLAG_NAMES, AGENT_MAPPING
    ├── models.py                 # Dataclasses voor State, Gate, Artefacts, Log
    ├── repository.py             # Atomic state.json I/O & logging
    ├── probes.py                 # Bestands- & visualcontrole
    ├── engine.py                 # State machine transitielogica & pre/postchecks
    ├── briefs.py                 # Agent instruction generator
    ├── formatters.py             # Markdown projecties & statustabellen
    └── service.py                # WorkflowService API (wordt aangeroepen door FastAPI & CLI)
```

---

## 4. Toekomstvisie & Uitbreidingen (Fase 2 & 3)

### 4.1 RAG-Corpus van Eerdere Artikelen
In een latere fase wordt de Web UI voorzien van een **RAG (Retrieval-Augmented Generation) index**:
- **Geïndexeerd Archief**: Alle eerdere artikelen van `edwinvandillen.nl` en achtergronddocumentatie worden gevectoriseerd en opgeslagen in een lokale/cloud vector database (bijv. ChromaDB of Qdrant).
- **Voeding voor de Onderzoeker**: Tijdens Modus 1 (Brainstorm) en Fase 1 (Outline) raadpleegt de `blogpost-onderzoeker` automatisch dit RAG-archief. Hierdoor kan de agent direct refereren naar eerdere artikelen, doublures voorkomen en historische definities hergebruiken.

### 4.2 Integratie met `jarvisje.com`
De bestaande AI-architectuur en digitale tweeling van **`jarvisje.com`** wordt geïntegreerd in de Web UI:
- **Digitale Tweeling Persona**: De Socratische Onderzoeker wordt verrijkt met de specifieke kennis, denkstijl en persona-instellingen van Jarvisje.
- **Gedeelde API Layer**: Een uniforme interface tussen de blogpost-orkestrator en het Jarvisje-ecosysteem.

---

## 5. Roadmap & Bouwfasen

```text
  Fase A: Refactoren Orchestrator ───► Fase B: FastAPI & Async Runner ───► Fase C: Web UI & Stepper ───► Fase D: RAG & Jarvisje
  (Opsplitsing orchestrate.py)         (REST API & WebSockets)             (React Dashboard & Chat)        (Vectorstore & Tweeling)
```

1. **Fase A · Refactoring Control Plane (Python Package)**
   - Opsplitsen van `scripts/orchestrate.py` naar het `orchestrator/` package.
   - Realiseren van de `WorkflowService` klasse.
   - Borgen dat de 34 unittests in `tests/test_orchestrate.py` 100% slagen.
2. **Fase B · FastAPI Server & Task Queue**
   - Bouwen van de REST API endpoints voor posts, fases, gates en vlaggen.
   - WebSockets toevoegen voor real-time streaming van subagent-uitvoer en status-updates.
3. **Fase C · Web UI Frontend**
   - Ontwikkelen van de browser-interface met het Dashboard, de Socratische Chat (Modus 1) en de Visuele Bolletjesketen Stepper (Modus 2).
4. **Fase D · RAG Corpus & Jarvisje Integratie**
   - Toevoegen van vector-indexering over het blogpost-archief.
   - Integratie met de `jarvisje.com` chat-engine en persona.
