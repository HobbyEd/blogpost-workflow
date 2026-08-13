# ADR-004: Hard vs Soft Quality Gates Strategy

* **Status**: Accepted
* **Datum**: 2026-08-11
* **Auteurs**: Edwin van Dillen

---

## 1. Context & Probleemstelling

In de redactionele workflow zitten verschillende controlepunten (gates). In YOLO-modus willen we dat de keten zo ver mogelijk automatisch doorloopt, maar er zijn specifieke momenten waarop automatische goedkeuring onaanvaardbare risico's met zich meebrengt (bijvoorbeeld onjuiste citaten live publiceren op edwinvandillen.nl).

Er is dus behoefte aan een onderscheid tussen poorten die in YOLO-modus automatisch mogen doorlopen (**Soft Gates**) en poorten die **altijd** menselijke goedkeuring of een expliciete vlag vereisen (**Hard Gates**).

---

## 2. Overwogen Alternatieven

1. **Alle Gates zijn Soft in YOLO**: YOLO slaat alle stopmomenten over.
   - *Nadeel*: Risico op fantoomcitaten, missende feitenchecks of ongewilde uploads.
2. **Alle Gates zijn Hard**: De mens moet bij elke fase op 'approve' klikken.
   - *Nadeel*: Neemt het nut van YOLO-automatisering volledig weg.
3. **Expliciet Onderscheid: Hard vs. Soft Gates (Gekozen)**.

---

## 3. Beslissing

We hanteren een strikte classificatie van kwaliteits-poorten:

- **Soft Gates** (Automatisch goedgekeurd in YOLO-modus):
  - `intake`, `outline`, `draft`, `style`, `series`, `critique`, `visuals`.
- **Hard Gates** (Stoppen ALTIJD, ook in YOLO-modus):
  - **`synthesis`**: Verifieert of Grok-review verwerkt is of expliciet overgeslagen (`skip_synthesis`).
  - **`factcheck`**: Verplicht aanwezigheid van `feitencheck.md` (of expliciet `skip_factcheck=true`). Geen fantoomcitaten live.
  - **`deploy`**: Verplicht expliciet akkoord (`deploy_approved=true`). Uitsluitend concept-upload (`status: draft`) op WordPress.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**:
  - 100% garantie dat fatale redactionele fouten (zoals onjuiste citaten) de live-omgeving nooit ongemerkt bereiken.
  - Hoge verwerkingssnelheid voor routinematige tussenstappen.
* **Negatief (-)**:
  - Gebruiker moet bij de `factcheck` en `deploy` fasen altijd een actie uitvoeren of een vlag zetten.
