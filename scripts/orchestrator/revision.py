"""De opmerkingen van de auteur na het lezen in WordPress (ADR-010 §3.4).

Het oordeelsmoment viel altijd buiten het systeem. Bij deel 2 kwamen de drie inhoudelijke
opmerkingen (de Sinek-sectie moet eruit, de visuals tekenen lagen als zuilen, het slot mist
een conclusie) pas nadat het concept in WordPress stond, en ze zijn nergens vastgelegd. Ze
bestonden alleen in een gesprek.

`revisie.md` maakt er een artefact van, met dezelfde status als de bevinding van een check:
zolang een opmerking openstaat, gaat er geen nieuwe deploy naar WordPress. Zo kan een
opmerking niet stilletjes verdampen tussen twee rondes.

Het bestand wordt door de orkestrator geschreven, niet door een agent. Het is de enige
plek in de keten waar de auteur zelf de invoer levert.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

REPORT = "revisie.md"

_JSON_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)


def parse_points(text: str) -> list[dict[str, Any]]:
    """Lees de opmerkingen uit revisie.md."""
    match = _JSON_FENCE.search(text)
    if not match:
        raise ValueError(
            f"{REPORT} bevat geen ```json-blok. Het bestand opent met een json-blok met "
            'een lijst "punten".'
        )
    try:
        blok = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Het json-blok in {REPORT} is geen geldige JSON: {e}") from None

    if not isinstance(blok, dict) or not isinstance(blok.get("punten"), list):
        raise ValueError(f'Het json-blok in {REPORT} moet een object met een lijst "punten" zijn.')

    return [_normalize(p, i) for i, p in enumerate(blok["punten"], 1)]


def _normalize(item: Any, idx: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"Opmerking {idx} in {REPORT} is geen object.")
    for veld in ("id", "opmerking"):
        if not str(item.get(veld) or "").strip():
            raise ValueError(f"Opmerking {idx} in {REPORT} mist {veld}.")
    return {
        "id": str(item["id"]).strip(),
        "waar": str(item.get("waar") or "").strip() or "hele post",
        "opmerking": str(item["opmerking"]).strip(),
        "afgehandeld": str(item.get("afgehandeld") or "").strip() or None,
        "at": item.get("at"),
    }


def read_points(post_dir: str) -> list[dict[str, Any]]:
    """Lees de opmerkingen van schijf. Geen bestand betekent geen opmerkingen."""
    pad = os.path.join(post_dir, REPORT)
    if not os.path.isfile(pad):
        return []
    with open(pad, encoding="utf-8") as f:
        return parse_points(f.read())


def open_points(punten: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """De opmerkingen die nog niet zijn afgehandeld."""
    return [p for p in punten if not p["afgehandeld"]]


def write(post_dir: str, punten: list[dict[str, Any]], titel: str) -> None:
    """Schrijf revisie.md: het json-blok voor de state machine, de tekst voor de mens."""
    blok = json.dumps({"punten": punten}, ensure_ascii=False, indent=2)
    regels = [
        f"# Revisiepunten — {titel}",
        "",
        "Opmerkingen van de auteur na het lezen van het concept in WordPress (ADR-010 §3.4).",
        "Zolang een punt openstaat, weigert `run deploy`.",
        "",
        "```json",
        blok,
        "```",
        "",
        "## Punten",
        "",
    ]
    if not punten:
        regels.append("Geen opmerkingen.")
    for p in punten:
        merk = "✓" if p["afgehandeld"] else "○"
        regels.append(f"- {merk} **{p['id']} · {p['waar']}** — {p['opmerking']}")
        if p["afgehandeld"]:
            regels.append(f"  - afgehandeld: {p['afgehandeld']}")

    with open(os.path.join(post_dir, REPORT), "w", encoding="utf-8") as f:
        f.write("\n".join(regels) + "\n")


def next_id(punten: list[dict[str, Any]]) -> str:
    """Geef het volgende vrije punt-id (r1, r2, ...)."""
    nummers = [int(m.group(1)) for p in punten if (m := re.fullmatch(r"r(\d+)", p["id"]))]
    return f"r{max(nummers, default=0) + 1}"


def add(post_dir: str, opmerking: str, waar: str, titel: str, tijdstip: str) -> dict[str, Any]:
    """Voeg een opmerking toe."""
    if not opmerking.strip():
        raise ValueError("Een opmerking zonder tekst zegt niets.")
    punten = read_points(post_dir)
    punt = {
        "id": next_id(punten),
        "waar": waar.strip() or "hele post",
        "opmerking": opmerking.strip(),
        "afgehandeld": None,
        "at": tijdstip,
    }
    punten.append(punt)
    write(post_dir, punten, titel)
    return punt


def close(post_dir: str, punt_id: str, hoe: str, titel: str) -> dict[str, Any]:
    """Markeer een opmerking als afgehandeld, met hoe."""
    if not hoe.strip():
        raise ValueError(
            "Zeg hoe de opmerking is verwerkt. Zonder dat is later niet na te gaan of ze "
            "echt is opgepakt of alleen weggeklikt."
        )
    punten = read_points(post_dir)
    punt = next((p for p in punten if p["id"] == punt_id), None)
    if punt is None:
        bekend = ", ".join(p["id"] for p in punten) or "geen"
        raise ValueError(f"Onbekend revisiepunt '{punt_id}'. Bekend: {bekend}.")
    punt["afgehandeld"] = hoe.strip()
    write(post_dir, punten, titel)
    return punt


def summarize(post_dir: str) -> dict[str, Any]:
    """Stand van de revisiepunten, voor de CLI en de UI."""
    punten = read_points(post_dir)
    openstaand = open_points(punten)
    return {
        "totaal": len(punten),
        "open": len(openstaand),
        "punten": punten,
    }
