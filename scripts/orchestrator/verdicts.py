"""Bevindingen uit de controlerapporten lezen (ADR-010 §6, stap 2).

Elke controlefase levert een rapport dat begint met een ```json-blok met een lijst
bevindingen. Daarmee kan de gate zelf vaststellen of er iets voor te leggen is. Zonder dat
signaal moest een mens elf keer per post "akkoord" klikken op controles die niets hadden
gevonden: 49 goedkeuringen, nul afwijzingen.

Twee zwaartes, en het onderscheid is de kern:

- **blocking** — een fout die weg moet. Een misquote, een verwijzing naar het verkeerde
  deel, een huisstijl-overtreding, meetwaarden buiten de band. De gate stopt.
- **advisory** — iets om te wegen, geen fout. De gate stopt niet, het staat in het rapport.

De stijl-check vindt in vrijwel elke ronde kandidaten die geen overtreding zijn. Zonder dit
onderscheid zou de gate altijd afgaan en verandert er niets aan de situatie die ADR-010
beschrijft.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

BLOCKING = "blocking"
ADVISORY = "advisory"
SEVERITIES = (BLOCKING, ADVISORY)

REQUIRED_FIELDS = ("severity", "categorie", "waar", "wat")

_JSON_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)


def parse_findings(text: str, bestandsnaam: str) -> list[dict[str, Any]]:
    """Lees de bevindingenlijst uit een controlerapport.

    Gooit ValueError als het blok ontbreekt, niet parseert of niet aan het formaat voldoet.
    Een leeg `findings` is geldig en betekent: niets gevonden.
    """
    match = _JSON_FENCE.search(text)
    if not match:
        raise ValueError(
            f"{bestandsnaam} bevat geen ```json-blok. Elk controlerapport opent met een "
            'json-blok met een lijst "findings"; een lege lijst betekent niets gevonden.'
        )
    try:
        blok = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Het json-blok in {bestandsnaam} is geen geldige JSON: {e}") from None

    if not isinstance(blok, dict) or "findings" not in blok:
        raise ValueError(f'Het json-blok in {bestandsnaam} moet een object met "findings" zijn.')

    rauw = blok["findings"]
    if not isinstance(rauw, list):
        raise ValueError(f'"findings" in {bestandsnaam} moet een lijst zijn.')

    return [_normalize(f, i, bestandsnaam) for i, f in enumerate(rauw, 1)]


def _normalize(item: Any, idx: int, bestandsnaam: str) -> dict[str, Any]:
    """Controleer één bevinding op volledigheid."""
    if not isinstance(item, dict):
        raise ValueError(f"Bevinding {idx} in {bestandsnaam} is geen object.")

    ontbreekt = [f for f in REQUIRED_FIELDS if not str(item.get(f) or "").strip()]
    if ontbreekt:
        raise ValueError(
            f"Bevinding {idx} in {bestandsnaam} mist {', '.join(ontbreekt)}. Elke bevinding "
            "noemt zwaarte, categorie, vindplaats en wat er aan de hand is."
        )

    severity = str(item["severity"]).strip().lower()
    if severity not in SEVERITIES:
        raise ValueError(
            f"Bevinding {idx} in {bestandsnaam} heeft zwaarte '{severity}'. "
            f"Gebruik {BLOCKING} of {ADVISORY}."
        )

    return {
        "severity": severity,
        "categorie": str(item["categorie"]).strip(),
        "waar": str(item["waar"]).strip(),
        "wat": str(item["wat"]).strip(),
        "suggestie": str(item.get("suggestie") or "").strip() or None,
    }


def read_report(post_dir: str, bestandsnaam: str) -> list[dict[str, Any]]:
    """Lees de bevindingen uit één rapport op schijf."""
    pad = os.path.join(post_dir, bestandsnaam)
    if not os.path.isfile(pad):
        raise FileNotFoundError(f"{bestandsnaam} ontbreekt in {post_dir}.")
    with open(pad, encoding="utf-8") as f:
        return parse_findings(f.read(), bestandsnaam)


def read_phase_findings(post_dir: str, phase: str) -> list[dict[str, Any]]:
    """Alle bevindingen van een controlefase, over al haar rapporten heen.

    De alignment-fase houdt haar eigen verdictformaat uit ADR-007; de discrepanties
    daaruit tellen als blocking. Zo hoeft die ADR niet open voor dit mechanisme.
    """
    from .constants import PHASE_REPORTS

    if phase == "alignment":
        from .archival_validator import read_alignment_verdict

        verdict = read_alignment_verdict(post_dir)
        return [
            {
                "severity": BLOCKING,
                "categorie": "archief-tegenspraak",
                "waar": d.get("historical_ref") or d["historical_slug"],
                "wat": d.get("toelichting") or "Tegenspraak met eerder gepubliceerd werk.",
                "suggestie": None,
            }
            for d in verdict["discrepancies"]
        ]

    bevindingen: list[dict[str, Any]] = []
    for bestandsnaam in PHASE_REPORTS.get(phase, ()):
        bevindingen.extend(read_report(post_dir, bestandsnaam))
    return bevindingen


def summarize(bevindingen: list[dict[str, Any]]) -> dict[str, Any]:
    """Vat bevindingen samen tot wat de gate en de statustabel nodig hebben."""
    blocking = sum(1 for b in bevindingen if b["severity"] == BLOCKING)
    return {
        "blocking": blocking,
        "advisory": len(bevindingen) - blocking,
        "status": "FINDINGS" if blocking else "OK",
        "findings": bevindingen,
    }


def collect_findings(post_dir: str, state: dict[str, Any]) -> dict[str, Any]:
    """Bundel de bevindingen van alle controlefases tot één overzicht (ADR-010 §6, stap 3).

    Bewust afgeleid op het moment van lezen, niet opgeslagen. Een opgeslagen bundel gaat
    verouderen zodra een rapport opnieuw draait, en dat is precies de fout die deze week
    drie keer is gevonden. De rapporten op schijf blijven de enige bron.

    Per fase wordt ook de actualiteit gemeld: hoort het rapport nog bij de huidige draft?
    """
    from .constants import CONDITIONAL_GATES, PHASE_ARTEFACT_KEY
    from .probes import probe_artefacts
    from .repository import stale_phases, unrecorded_phases

    probed = probe_artefacts(post_dir)
    verouderd = set(stale_phases(state, post_dir, CONDITIONAL_GATES))
    ongeregistreerd = set(unrecorded_phases(state, CONDITIONAL_GATES))

    fases: list[dict[str, Any]] = []
    alle: list[dict[str, Any]] = []

    for phase in CONDITIONAL_GATES:
        artefact = PHASE_ARTEFACT_KEY.get(phase)
        if artefact and probed.get(artefact) != "present":
            fases.append({"phase": phase, "staat": "niet gedraaid", "blocking": 0, "advisory": 0})
            continue

        try:
            bevindingen = read_phase_findings(post_dir, phase)
        except (FileNotFoundError, ValueError) as e:
            fases.append({"phase": phase, "staat": "onleesbaar", "fout": str(e), "blocking": 0, "advisory": 0})
            continue

        if phase in verouderd:
            staat = "verouderd"
        elif phase in ongeregistreerd:
            staat = "geen vingerafdruk"
        else:
            staat = "actueel"

        samenvatting = summarize(bevindingen)
        fases.append({
            "phase": phase,
            "staat": staat,
            "blocking": samenvatting["blocking"],
            "advisory": samenvatting["advisory"],
        })
        for b in bevindingen:
            alle.append({**b, "phase": phase})

    # De opmerkingen van de auteur horen in hetzelfde overzicht: ze hebben dezelfde
    # status als een bevinding en houden de deploy net zo goed tegen (ADR-010 §3.4).
    from .revision import open_points as revisie_open
    from .revision import read_points as revisie_punten

    try:
        openstaand = revisie_open(revisie_punten(post_dir))
    except ValueError as e:
        fases.append({"phase": "revisie", "staat": "onleesbaar", "fout": str(e), "blocking": 0, "advisory": 0})
        openstaand = []
    else:
        if openstaand:
            fases.append({
                "phase": "revisie", "staat": "actueel",
                "blocking": len(openstaand), "advisory": 0,
            })
        for p in openstaand:
            alle.append({
                "severity": BLOCKING,
                "categorie": "opmerking van de auteur",
                "waar": p["waar"],
                "wat": p["opmerking"],
                "suggestie": None,
                "phase": "revisie",
            })

    # Blokkerend eerst; daarbinnen op fasevolgorde zoals de keten ze aflegt.
    volgorde = {p: i for i, p in enumerate(CONDITIONAL_GATES)}
    volgorde["revisie"] = -1  # jouw eigen opmerkingen bovenaan
    alle.sort(key=lambda b: (b["severity"] != BLOCKING, volgorde.get(b["phase"], 99)))

    return {
        "blocking": sum(1 for b in alle if b["severity"] == BLOCKING),
        "advisory": sum(1 for b in alle if b["severity"] == ADVISORY),
        "phases": fases,
        "findings": alle,
    }


def render_findings_md(bundel: dict[str, Any]) -> str:
    """Maak het bevindingenoverzicht leesbaar voor de terminal en de UI."""
    regels = [
        f"**{bundel['blocking']} blokkerend, {bundel['advisory']} ter overweging**",
        "",
        "| Fase | Staat | Blokkerend | Ter overweging |",
        "|---|---|---|---|",
    ]
    for f in bundel["phases"]:
        regels.append(f"| {f['phase']} | {f['staat']} | {f['blocking']} | {f['advisory']} |")

    if bundel["findings"]:
        regels += ["", "## Bevindingen", ""]
        for b in bundel["findings"]:
            merk = "🔴" if b["severity"] == BLOCKING else "🟡"
            regels.append(f"- {merk} **{b['phase']} · {b['categorie']}** ({b['waar']}) — {b['wat']}")
            if b.get("suggestie"):
                regels.append(f"  - suggestie: {b['suggestie']}")
    else:
        regels += ["", "Geen bevindingen."]

    # Altijd tonen, ook als er geen bevindingen zijn: een onleesbaar rapport telt nul
    # bevindingen, en zonder deze sectie leest dat als "niets gevonden".
    onleesbaar = [f for f in bundel["phases"] if f["staat"] == "onleesbaar"]
    if onleesbaar:
        regels += ["", "## Niet te lezen", ""]
        regels += [f"- **{f['phase']}** — {f['fout']}" for f in onleesbaar]

    verouderd = [f for f in bundel["phases"] if f["staat"] == "verouderd"]
    if verouderd:
        regels += ["", "## Verouderd", ""]
        regels += [
            f"- **{f['phase']}** — het rapport hoort bij een oudere versie van draft.md"
            for f in verouderd
        ]

    return "\n".join(regels)


def has_blocking(state: dict[str, Any], phase: str) -> bool:
    """True als de laatst vastgelegde uitkomst van deze fase een blokkerende bevinding had."""
    return bool(((state.get("verdicts") or {}).get(phase) or {}).get("blocking"))
