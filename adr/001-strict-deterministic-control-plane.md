# ADR-001: Strict Deterministic Control Plane in Python

* **Status**: Accepted
* **Datum**: 2026-08-11
* **Auteurs**: Edwin van Dillen

---

## 1. Context & Probleemstelling

Bij het bouwen van agentic workflows (zoals het redactioneel schrijven van kwalitatieve blogposts) is er een fundamenteel risico dat LLM's fasen overslaan, niet-bestaande bronnen hallucineren of beslissingslogica stilzwijgend negeren als het proces puur in LLM-prompts wordt gedefinieerd.

Om redactionele kwaliteit te waarborgen hebben we een mechanisme nodig dat strak toeziet op de juiste volgorde van fasen, verplichte schijf-artefacten controleert en menselijke goedkeuringspoorten afdwingt.

---

## 2. Overwogen Alternatieven

1. **Puur Prompt-Gedreven Orkestratie**: De hoofd-LLM leest een systeem-prompt en roept sub-prompts aan naar eigen inzicht.
   - *Nadeel*: Onvoorspelbaar, ontestbaar, neigt naar hallucinaties bij lange sessies.
2. **Heavyweight Workflow Frameworks (Airflow / Temporal)**: Gebruik maken van enterprise workflow engines.
   - *Nadeel*: Overkill voor redactionele agent-ketens; vereist externe databases en zware infrastructuur.
3. **Strikte Python Control Plane & State Machine (Gekozen)**: Een lichtgewicht Python script/service die de fasen en transitiegrafiek deterministisch beheert via `state.json` en schijf-probes.

---

## 3. Beslissing

We kiezen voor een **Strikte Deterministische Control Plane in Python**.

- De orkestrator beheert de enige bron van waarheid (`posts/<slug>/state.json`) en controleert bij elke stap via bestands-probes of de vereiste markdown-bestanden op schijf staan.
- LLM's voeren uitsluitend de content-taken binnen één fase uit; zij hebben geen zeggenschap over de procesovergangen of statusveranderingen.
- De transitielogica is 100% unit-testbaar zonder afhankelijkheid van externe LLM-API's.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**:
  - 100% voorspelbare en reproduceerbare procesafhandeling.
  - LLM kan de pijplijn nooit 'per ongeluk' laten doorlopen zonder benodigde tussenkwaliteit.
  - Volledig lokaal testbaar via Python unit tests.
* **Negatief (-)**:
  - Nieuwe uitzonderingen of pijplijn-fases vereisen expliciete code-aanpassingen in de Python engine.
