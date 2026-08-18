# ADR-003: Two-Phase Workflow — Interactive Brainstorm vs YOLO Stepper Engine

* **Status**: Accepted
* **Datum**: 2026-08-12
* **Auteurs**: Edwin van Dillen

---

## 1. Context & Probleemstelling

Bij het schrijven van een blogpost of een artikelenreeks is er een scherp onderscheid tussen twee creatieve fases:
1. **De Vormgevingsfase (Brainstorm)**: Het verkennen van het onderwerp, bepalen van de invalshoek en thesis via een socratische dialoog.
2. **De Executiefase (Productie)**: Het strak doorlopen van de redactionele keten (outline, draft, stijl, critique, visuals, factcheck, deploy).

Als een AI-agent direct in 'productiemodus' springt zonder dat de uitgangspunten helder zijn, ontstaat er een artikel van lage kwaliteit. Omgekeerd, als de gebruiker tijdens de productiefase bij elke tussenstap handmatig commando's moet invoeren, gaat de snelheid verloren.

---

## 2. Overwogen Alternatieven

1. **Volledig Handmatig (Stap-voor-Stap)**: Bij elke stap handmatig de agent aanroepen via terminal commando's.
   - *Nadeel*: Te veel frictie en herhalend werk.
2. **Volledig Automatisch (Black Box Autonomous)**: Eén prompt invoeren en de AI maakt een complete post zonder tussenstops.
   - *Nadeel*: Geen controle over de redactionele rigueur, de huisstijl of de broncontrole.
3. **Tweedelige Hybride Architectuur (Gekozen)**: Interactive Co-Creation Mode & YOLO Stepper Engine.

---

## 3. Beslissing

We splitsen de gebruikerservaring op in twee duidelijke modi:

- **Modus 1 — Interactive Co-Creation Mode**:
  Een socratische dialoog tussen de auteur en de `blogpost-onderzoeker`. Uitkomsten worden vastgelegd in een **Uitgangspuntendocument** (`briefing.md`).
- **Modus 2 — YOLO Stepper Executie Engine**:
  Zodra de briefing klaar is, voert de orkestrator in YOLO-modus de agent-keten automatisch uit. De UI toont de status via een visuele **bolletjesketen (Stepper)**.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**:
  - Maximale redactionele controle aan de voorkant (briefing).
  - Maximale snelheid en automatisering tijdens de uitwerking (YOLO).
* **Negatief (-)**:
  - De Web UI moet twee verschillende interactievormen ondersteunen (Chat UI + Stepper Dashboard).

---

## 5. Bijwerking 2026-08-18 (ADR-010)

De stepper is geen lineaire voortgangsbalk meer.

- Boven de elf bolletjes staan de drie blokken uit ADR-010 (Richten, Bouwen, Oordelen).
- Een bolletje is klikbaar: het opent het artefact van die stap. Outline is de enige stap
  waar je vanaf een latere fase naartoe terug kunt met een verplichte opmerking.
- Tabs volgen de rapporten op schijf, niet een hard gecodeerde subset. Stijl, reeks,
  synthese en visuals waren tot 17 augustus onzichtbaar terwijl de bestanden er lagen.
- YOLO in modus 2 betekent: sla het klikken over als er niets te beslissen valt. Een
  blocking-bevinding of een synthesepunt is wél iets te beslissen. De keten stopt dan,
  met de reden in beeld.

Modus 1 (brainstorm) is ongewijzigd.
