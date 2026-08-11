---
slug: <slug>
titel: <werktitel>
aangemaakt: <YYYY-MM-DD>
huidige_fase: 1-outline
yolo_mode: uit
---

# Staat — <werktitel>

Dit is het staat-manifest van deze blogpost. De orkestrator leest en werkt dit
bestand bij. Het legt vast in welke fase de post zit en welke artefacten klaar
zijn, zodat het werk hervatbaar is over meerdere sessies.

## Fasen (Fase A + B + C)

| Fase | Stap | Status | Artefact |
|------|------|--------|----------|
| 0 | Intake | gereed | (deze map + dit bestand) |
| 1 | Outline en verrijking | open | outline.md |
| 2 | Draft schrijven | open | draft.md |
| 2b | Stijl-controle | open | (rapport in beslislog) |
| 2c | Reeks-consistentie | open | (rapport in beslislog) |
| 3 | Kritiek (Grok) | open | grok-feedback.md |
| 4 | Synthese | open | synthese.md |
| 5 | Visuals | open | visuals/ |
| 6 | Deploy (concept) | open | (edit-URL in beslislog) |

Statuswaarden: `open`, `bezig`, `gereed`, `afgekeurd`.

## Modus

`yolo_mode: uit` (standaard) — de orkestrator stopt bij elke gate en stelt
wijzigingen voor. `yolo_mode: aan` — safe-to-fail probes (artefact-genererende
stappen binnen deze map) draait de orkestrator zelfstandig en chaint door; harde
gates (publiceren, redactionele oordeelskeuzes) blijven staan. Zie de sectie
"Modus: yolo of voorstel" in `SKILL.md`.

## Volgende actie

Onderzoeker-subagent aanroepen voor de outline.

## Beslislog

Elke gate-beslissing hier vastleggen: datum, fase, beslissing (doorgaan /
bijsturen / opnieuw), en een korte reden.

- <YYYY-MM-DD> — Fase 0 — intake afgerond, onderwerp vastgesteld.
