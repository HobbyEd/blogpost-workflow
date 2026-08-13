# ADR-002: Modular Orchestrator Service Package

* **Status**: Accepted
* **Datum**: 2026-08-12
* **Auteurs**: Edwin van Dillen

---

## 1. Context & Probleemstelling

Oorspronkelijk was de orkestrator geïmplementeerd als één groot CLI-script (`scripts/orchestrate.py` van ruim 1.600 regels). Naarmate het proces groeide en het besluit werd genomen om een Web UI backend te bouwen, ontstond het risico op dubbele code en koppeling tussen de terminal CLI-parser en de bedrijfslogica.

De Web UI en de CLI moeten exact dezelfde state-machine, pre-checks, post-checks en transitiegrafiek aanspreken zonder subprocessen af te hoeven vuren.

---

## 2. Overwogen Alternatieven

1. **CLI Subprocessen Aanroepen vanuit Web Backend**: De Web UI vuurt `subprocess.run(["python3", "scripts/orchestrate.py", ...])` aan.
   - *Nadeel*: Traag, kwetsbaar voor string parsing van terminal output, lastig om gestructureerde JSON uit te wisselen.
2. **Monolithische Refactor in Script**: De CLI-code opsplitsen in losse helperbestanden binnen de `scripts/` map.
   - *Nadeel*: Geen duidelijke grens tussen de CLI-laag en de herbruikbare API.
3. **Modulair Python Package met `WorkflowService` API (Gekozen)**: De logica isoleren in een `scripts/orchestrator/` package en de CLI transformeren naar een dunne wrapper.

---

## 3. Beslissing

We splitsen `scripts/orchestrate.py` op in het modulaire package **`scripts/orchestrator/`**:

- `service.py`: Exporteert de klasses **`WorkflowService`**, die een schone, type-annotated Python API biedt voor zowel de CLI als de aanstaande Web API backend.
- `engine.py`, `repository.py`, `probes.py`, `briefs.py`, `formatters.py`, `constants.py`: Scheiding van verantwoordelijkheden (Single Responsibility Principle).
- `scripts/orchestrate.py` blijft behouden als een dunne CLI-wrapper (minder dan 150 regels) voor achterwaartse compatibiliteit.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**:
  - De Web UI (FastAPI) en de CLI delen 100% dezelfde business logic.
  - Directe Python API in-memory maakt het testen supersnel (46 unit tests draaien in ~4 seconden).
  - Helder onderhoudbare code zonder diepe `if-else` geneste structuren.
* **Negatief (-)**:
  - Meer losse Python modules te beheren binnen `scripts/orchestrator/`.
