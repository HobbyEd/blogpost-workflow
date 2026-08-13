# Architectural Decision Records (ADR)

Welkom bij de Architectural Decision Records van het **Blogpost Workflow & Agent Platform**.

In deze map leggen we alle architecturele en technische keuzes vast (ADR's), inclusief de context, motivering en consequenties van elke beslissing.

---

## 🏛️ Overzicht van ADR's

| Nummer | Titel | Status | Datum |
|---|---|---|---|
| [`00`](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/00-overall-design-blogpost-webui.md) | **Overall Design Document: Web UI & Agent Platform** | Accepted | 2026-08-12 |
| `001` | [Strict Deterministic Control Plane in Python](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/001-strict-deterministic-control-plane.md) | Proposed | 2026-08-13 |
| `002` | [Modular Orchestrator Service Package](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/002-modular-orchestrator-service-package.md) | Proposed | 2026-08-13 |
| `003` | [Two-Phase Workflow — Interactive Brainstorm vs YOLO Stepper Engine](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/003-two-phase-interactive-yolo-workflow.md) | Proposed | 2026-08-13 |
| `004` | [Hard vs Soft Quality Gates Strategy](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/004-hard-soft-quality-gates-strategy.md) | Proposed | 2026-08-13 |
| `005` | [Bulk Research Protocol & Local Source Fetching Tooling](file:///Users/evdillen/edwinvandillen@gmail.com%20-%20Google%20Drive/My%20Drive/16.%20AI/03.%20Blogpost/01.%20Blogpost%20agents/adr/005-bulk-research-protocol-and-source-fetching.md) | Proposed | 2026-08-13 |

---

## 📝 ADR Format & Sjabloon

Elke nieuwe ADR gebruikt de volgende vaste structuur:

```markdown
# ADR-00X: [Titel van de beslissing]

* **Status**: Proposed | Accepted | Deprecated | Superseded by ADR-00Y
* **Datum**: YYYY-MM-DD
* **Auteurs**: Edwin van Dillen

## 1. Context & Probleemstelling
[Welke uitdaging of architectureel vraagstuk noopt tot deze keuze?]

## 2. Overwogen Alternatieven
- Alternatief A: [...]
- Alternatief B: [...]

## 3. Beslissing
[Welke optie is gekozen en waarom?]

## 4. Consequenties & Trade-offs
* **Positief (+)**: [...]
* **Negatief (-)**: [...]
* **Risico's**: [...]
```
