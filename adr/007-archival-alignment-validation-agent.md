# ADR-007: Pre-Deploy Archief-Consistentie Agent & Discrepantie Decision Gate

* **Status**: Accepted
* **Datum**: 2026-08-14 (samengevoegd; oorspronkelijk 2026-08-13)
* **Auteurs**: Edwin van Dillen
* **Gerelateerd**: [ADR-004 (Hard vs Soft Gates)](004-hard-soft-quality-gates-strategy.md), [ADR-006 (Local RAG Archiefindex)](006-local-rag-vectorstore-blog-archive.md), [ADR-008 (Admin Settings & Background Indexer)](008-admin-settings-tab-and-background-rag-indexer.md)
* **Vervangt**: ADR-009 (Pre-Deploy Subject Alignment/Disalignment Agent & Discrepancy Gate), samengevoegd in deze ADR op 2026-08-14

> **Samenvoeging.** ADR-007 en ADR-009 beschreven dezelfde agent op dezelfde plek in de
> keten. ADR-007 legde vast **wanneer** hij draait en waarom; ADR-009 legde vast **hoe** hij
> werkt (RAG-retrieval, decision gate, datamodel, endpoints). Twee ADR's voor één beslissing
> leverde twee artefactnamen op voor één rapport (`archiefcheck.md` naast
> `archief-consistentie.md`) en twee endpoint-namen die geen van beide klopten. Alles staat
> nu hier; ADR-009 is verwijderd.

---

## 1. Context & Probleemstelling

Ook als de onderzoeker en de schrijver de RAG-archiefindex (ADR-006) gebruiken, kan een
nieuwe post vlak voor publicatie afwijken van een eerder ingenomen standpunt of een eerder
vastgelegde definitie. Er zijn twee situaties, en ze vragen tegengestelde acties:

1. **Onbedoelde tegenspraak.** De agent of de auteur spreekt ongemerkt een eerdere post
   tegen. Dat schaadt de geloofwaardigheid en moet terug naar de draft.
2. **Voortschrijdend inzicht.** De auteur herziet bewust een eerdere stelling op grond van
   nieuwe ervaring of veranderde techniek. Dat is waardevol, mits het in het artikel
   expliciet als herziening wordt geframed en onderbouwd.

Het systeem kan dit onderscheid niet zelf maken: het verschil zit in de bedoeling van de
auteur, niet in de tekst. Wat het systeem wél kan, is de afwijking vinden en de auteur
dwingen te kiezen. Dat is de rol van deze agent.

---

## 2. Overwogen Alternatieven

1. **De reeks-consistentie-check (fase 2c) alles laten doen.** Die agent uitbreiden zodat
   hij ook het hele archief toetst.
   - *Nadeel*: fase 2c draait vroeg, op de ruwe draft. Pas na kritiek, synthese en
     feitencheck staat de definitieve tekst vast. Een toets op een tekst die daarna nog
     verandert, toetst niet wat er gepubliceerd wordt.
2. **Handmatige controle bij publicatie.** De auteur loopt de eerdere posts uit het hoofd na.
   - *Nadeel*: foutgevoelig, en het schaalt niet bij 61 posts.
3. **Een aparte pre-deploy validatie-agent `archief-consistentie-check` (gekozen).**

---

## 3. Beslissing

### 3.1 Positie in de keten

De agent draait als **fase 5c**, direct na de bron- en feitencheck en vóór de deploy-gate:

```
 [5b: Factcheck] ➔ [5c: Archief-consistentie-check] ➔ [Decision gate] ➔ [6: Deploy]
                             |
                             v
                   RAG-archiefindex (ADR-006)
                             |
               +-------------+-------------+
               |                           |
        [ALIGNMENT_OK]           [DISCREPANCY_DETECTED]
               |                           |
      automatisch akkoord        waarschuwing + decision gate
                                           |
                              +------------+------------+
                              |                         |
                  [voortschrijdend inzicht]     [inhoudelijke fout]
                              |                         |
                    accepteer met notitie        terug naar draft
                              |                         |
                        door naar deploy          concept herstellen
```

Dit is een **harde gate** (ADR-004): ook in `yolo_mode` blijft de menselijke beslissing
verplicht zodra er een afwijking is gevonden. Een inhoudelijke tegenspraak mag nooit
stilzwijgend doorglippen.

### 3.2 Uitvoerder, analyse en modelkeuze

De beoordeling doet de **subagent `archief-consistentie-check`**, niet de Python-code.
Dat is dezelfde constructie als bij `stijl-check`, `bron-check` en
`reeks-consistentie-check`: de agent doet het inhoudelijke werk en schrijft een rapport,
de control plane leest dat rapport en zet de gate. Zo blijft er één uitvoeringspad in de
keten en is er geen API-sleutel of extra dependency nodig. De prijs is dat fase 5c alleen
draait als de orkestrator draait; dat geldt voor elke andere fase ook.

De agent legt het concept (`draft.md`, anders `synthese.md`) naast het archief:

1. **Ophalen**: `scripts/rag_cli.py search` per kernstelling, niet één keer op het
   onderwerp. Een tegenspraak zit in een stelling, niet in een thema. Daarnaast
   `reference/corpus-inventaris.md` als vangnet onder het lexicale zoeken.
2. **Beoordelen**: de agent vergelijkt de kernstellingen, begrippen en conclusies van het
   concept met die passages.
3. **Classificatie**:
   - `ALIGNMENT_OK` — de inhoud sluit aan bij eerdere publicaties, of wijkt af en legt die
     afwijking in de tekst zelf expliciet uit als herziening.
   - `DISCREPANCY_DETECTED` — er is een tegenstrijdige bewering of een gewijzigde definitie,
     zonder dat het artikel de afwijking erkent.

**Model: Sonnet 5** (`model: sonnet` in de agentdefinitie). De vergelijking vraagt om
inhoudelijk redeneren over genuanceerde stellingen, niet om trefwoordvergelijking. Sonnet
is daarvoor toereikend en sneller en goedkoper dan Opus; dit is een controlestap, geen
schrijfstap.

**De gate gaat alleen af bij een geciteerd paar.** Het model moet bij elke gemelde
tegenstrijdigheid beide citaten geven: de zin uit het concept en de zin uit de eerdere post.
Kan het die niet geven, dan is er geen bevinding. Zonder die eis rapporteert de gate
vermoedens, en een gate die vermoedens rapporteert wordt binnen drie posts weggeklikt.

**Een lage gelijkenisscore is geen bevinding.** Een lage score betekent dat een passage
weinig met het stuk te maken heeft, niet dat hij het tegenspreekt. Retrieval bepaalt alleen
wélke passages worden voorgelegd; de beoordeling doet het model.

### 3.3 Decision gate in de Web UI

Bij `DISCREPANCY_DETECTED`:

1. De fase krijgt in de stepper een amber status met de badge
   `⚠️ Inhoudelijke discrepantie gevonden`.
2. Het viewer-paneel toont de vergelijking met de eerdere post, met beide citaten.
3. De auteur kiest expliciet uit twee opties:

   * **Accepteer als voortschrijdend inzicht** — de afwijking is bewust en correct. Een
     toelichting is **verplicht**; die wordt vastgelegd in `state.json` en in
     `archief-consistentie.md`. De gate gaat op groen.
   * **Wijs af als inhoudelijke fout** — de gate wordt afgekeurd, de post gaat terug naar
     `phase: draft` met `status: ready`. Het rapport blijft staan als input voor de
     correctie.

### 3.4 Artefact, datamodel en endpoints

**Artefactnaam: `posts/<slug>/archief-consistentie.md`.** Dit is de enige naam. ADR-007
sprak eerder van `archiefcheck.md`; die naam is vervallen. `archief-consistentie.md` is wat
`constants.py`, `engine.py` en de tests gebruiken.

Het rapport **begint met een ```json-blok**: dat is het verdict dat de state machine leest.
De proza eronder is voor de auteur. Zonder dat blok, of met een bevinding waarin een van
beide citaten ontbreekt, weigert `complete alignment` het rapport. Zo kan een half of leeg
rapport de gate niet passeren.

```json
{
  "status": "DISCREPANCY_DETECTED",
  "discrepancies": [
    {
      "historical_slug": "intentie-1-waarom-intentie-waarde-draagt",
      "historical_ref": "https://edwinvandillen.nl/?p=500",
      "previous_text": "…citaat uit de eerdere post…",
      "current_text": "…citaat uit het concept…",
      "toelichting": "waarom deze twee elkaar tegenspreken"
    }
  ]
}
```

`state.json` krijgt hetzelfde blok onder `archival_alignment`, aangevuld met `checked_at`
en, na de beslissing van de auteur, `resolution`:

```json
{
  "archival_alignment": {
    "status": "RESOLVED_PROGRESSIVE_INSIGHT",
    "discrepancies": ["… zoals hierboven …"],
    "checked_at": "2026-08-14T09:12:00+00:00",
    "resolution": {
      "type": "progressive_insight",
      "author_note": "Voortschrijdend inzicht t.o.v. deel 1",
      "resolved_at": "2026-08-14T09:20:00+00:00"
    }
  }
}
```

De fase loopt via de gewone lus, net als elke andere fase: `run alignment` levert de brief,
de agent schrijft het rapport, `complete alignment` valideert het verdict en zet de gate.

REST-endpoints, zoals ze in `server.py` heten:

- `POST /api/posts/{slug}/validate-alignment` — leest het verdict uit het rapport in
  `state.json`. Voert de check niet uit; zonder rapport volgt een 404.
- `POST /api/posts/{slug}/resolve-alignment` — verwerkt de beslissing van de auteur:
  ```json
  { "action": "progressive_insight | error_rejected", "note": "toelichting" }
  ```
  `note` is verplicht bij `progressive_insight`.

---

## 4. Implementatiestatus (2026-08-14)

De implementatie volgt deze ADR. Wat er is:

| Onderdeel | Vindplaats |
|---|---|
| Subagent die beoordeelt | `.claude/agents/archief-consistentie-check.md` |
| Brief met de RAG-stap | `briefs.py`, fase `alignment` |
| Verdict lezen en valideren | `archival_validator.py` (`parse_alignment_report`) |
| Geciteerd paar afdwingen | `archival_validator.REQUIRED_DISCREPANCY_FIELDS` |
| Voorwaardelijk harde gate | `engine.gate_type` en `engine.maybe_auto_approve` |
| Beslissing van de auteur | `archival_validator.resolve_alignment_discrepancy` |
| Tests | `tests/test_orchestrator_service.py::TestServiceAlignmentGate` |

Wat er **was**, en wat eraan is veranderd: de detectie was één regel,
`if match["score"] < 0.25`, met de logica omgekeerd — een lage gelijkenisscore werd
gerapporteerd als tegenspraak, dus de gate ging af op juist de minst relevante treffers.
Het rapport vermeldde "Claude 3.5 Sonnet" terwijl er geen model aan te pas kwam. En in de
discrepantie-tak werd `state["phase"]` niet op `alignment` gezet, waardoor de Web UI de
keuzeknoppen niet toonde: de enige uitkomst die de gate bestaansrecht gaf, liep vast. Alle
drie zijn verholpen; `archival_validator.py` beoordeelt niets meer zelf.

Openstaand: de gate draait alleen als de orkestrator draait. Zodra blok C een
altijd-aan-uitvoerder oplevert, verandert dat vanzelf; deze ADR hoeft daar niet voor om.

---

## 5. Consequenties & Trade-offs

* **Positief (+)**
  - Voorkomt dat de auteur ongemerkt een eerdere stelling tegenspreekt.
  - Maakt van een herziening een expliciete, vastgelegde keuze in plaats van een stille
    inconsistentie; de evolutie van inzichten is later te herleiden uit `state.json`.
  - De harde gate zorgt dat een afwijking ook in `yolo_mode` een mens passeert.
* **Negatief (-)**
  - Een extra stap plus een modelaanroep vlak voor publicatie.
  - De agent moet stijlverschillen en herformuleringen niet als inhoudelijke tegenspraak
    aanmerken. De eis van een geciteerd paar is de rem daarop.
* **Risico's**
  - Een gate die te vaak ten onrechte afgaat, wordt weggeklikt en is dan erger dan geen
    gate. Meet hoe vaak hij afgaat en hoe vaak de auteur "inhoudelijke fout" kiest; blijft
    dat laatste structureel uit, dan staat de drempel verkeerd.
  - De check is zo goed als de retrieval eronder. Lexicaal zoeken vindt een eerdere stelling
    in andere woorden niet (ADR-006); `reference/corpus-inventaris.md` is het vangnet.
