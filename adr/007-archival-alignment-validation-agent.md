# ADR-007: Pre-Deployment Archival Alignment Validation Agent

* **Status**: Proposed
* **Datum**: 2026-08-13
* **Auteurs**: Edwin van Dillen

---

## 1. Context & Probleemstelling

Zelfs als de onderzoeker en schrijver gebruikmaken van de lokale RAG-vectorstore (ADR-006), kan het voorkomen dat een nieuw geschreven blogpost vlak voor publicatie afwijkt van eerder ingenomen standpunten of gedefinieerde concepten.

Er zijn twee situaties mogelijk wanneer een nieuwe post afwijkt van het archief:
1. **Onbedoelde Inconsistentie / Tegenspraak**: De agent of auteur spreekt zichzelf ongemerkt tegen ten opzichte van een eerdere post. Dit schaadt de geloofwaardigheid.
2. **Voortschrijdend Inzicht (Gevalideerde Afwijking)**: De auteur herzien bewust een eerdere stelling op basis van nieuwe ervaringen of evoluerende technologie. Dit is waardevol, mits het in het artikel expliciet wordt geframed en onderbouwd als een voortschrijdend inzicht.

Er is behoefte aan een specifieke validatie-agent vlak vóór publicatie die dit onderscheid automatisch toetst.

---

## 2. Overwogen Alternatieven

1. **Reeks-consistentie-check (Fase 2c) alles laten doen**: De bestaande Fase 2c agent uitbreiden om ook het hele archief te toetsen.
   - *Nadeel*: Fase 2c draait vroeg op de ruwe draft. Pas na de kritiek-, synthese- en feitencheck-fasen staat de definitieve tekst vast.
2. **Handmatige Controle bij Publish**: De menselijke auteur vragen om alle eerdere posts uit het hoofd na te lopen.
   - *Nadeel*: Foutgevoelig en niet schaalbaar bij een groot archief.
3. **Dedicated Pre-Deployment Validatie-Agent `archief-consistentie-check` (Gekozen)**.

---

## 3. Beslissing

We voegen een nieuwe validatie-agent toe aan de keten: **`archief-consistentie-check`** (Fase 5c, direct na de Bron- & Feitencheck en vóór de Deploy-gate):

- **Inhoudelijke Toetsing**: De agent befragt de RAG Vectorstore (ADR-006) en vergelijkt de kernboodschap, definities en argumentatie van de concept-post met alle reeds gepubliceerde artikelen.
- **Beoordelingslogica op Afwijkingen**:
  - *Consistent*: De stelling sluit naadloos aan bij eerdere artikelen &rarr; **Akkoord 🟢**.
  - *Voortschrijdend Inzicht*: De stelling wijkt af, maar het artikel legt expliciet uit *waarom* het inzicht is geëvolueerd (bijv. "In deel 1 stelden we X, maar door ervaring Y zien we nu dat Z...") &rarr; **Valide Afwijking / Akkoord 🟢**.
  - *Onbedoelde Tegenspraak*: De stelling spreekt een eerdere post tegen zonder dat de afwijking erkend of gemotiveerd wordt &rarr; **Vlag / Rapportage in `archiefcheck.md` 🔴**.

---

## 4. Consequenties & Trade-offs

* **Positief (+)**:
  - Voorkomt dat de auteur ongemerkt eerdere stellingen tegenspreekt.
  - Stimuleert transparant schrijven over lerend vermogen en voortschrijdend inzicht.
  - Vormt een sterke kwaliteitsborging voor de langetermijn-visie van het platform.
* **Negatief (-)**:
  - Een extra agent-stap in de keten vlak voor publicatie (vergt korte extra executietijd).
