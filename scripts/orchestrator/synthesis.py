"""De synthese als beslismoment per punt (ADR-010 §3.3).

De synthese was een weegstap: de agent leverde per kritiekpunt een advies met
alternatieven, en de auteur ging akkoord met het geheel. Bij deel 2 van de intentie-reeks
bood punt 1 expliciet aan om sectie 7 te schrappen, als alternatief C. Het advies luidde
A, behouden en herkaderen, en dat is gevolgd. De sectie bleef staan en werd langer.

Daar zit een systematische druk achter. Grok becommentarieert per sectie, dus zijn punten
gaan over hoe een sectie beter kan, niet over of ze moet bestaan. Een synthese die per punt
een variant aanbeveelt, vertaalt dat in aanpassingen. Elke ronde maakt de tekst langer.

Daarom drie dingen, mechanisch afgedwongen in plaats van opgeschreven als voornemen:

1. De agent legt de varianten **neutraal** voor met hun gevolg. Geen aanbeveling.
2. **Verwerpen is bij elk punt een optie**, even zichtbaar als aannemen.
3. De auteur beslist **per punt**. Een motivering mag, is niet verplicht.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

REPORT = "synthese.md"
VERWERPEN = "verwerpen"

_JSON_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)


def parse_points(text: str) -> list[dict[str, Any]]:
    """Lees de punten uit synthese.md.

    Gooit ValueError als het blok ontbreekt of niet aan het formaat voldoet. Een lege
    lijst is geldig: er viel niets te wegen.
    """
    match = _JSON_FENCE.search(text)
    if not match:
        raise ValueError(
            f"{REPORT} bevat geen ```json-blok. De synthese opent met een json-blok met "
            'een lijst "points"; een lege lijst betekent dat er niets te wegen viel.'
        )
    try:
        blok = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Het json-blok in {REPORT} is geen geldige JSON: {e}") from None

    if not isinstance(blok, dict) or "points" not in blok:
        raise ValueError(f'Het json-blok in {REPORT} moet een object met "points" zijn.')
    if not isinstance(blok["points"], list):
        raise ValueError(f'"points" in {REPORT} moet een lijst zijn.')

    punten = [_normalize(p, i) for i, p in enumerate(blok["points"], 1)]

    ids = [p["id"] for p in punten]
    dubbel = {i for i in ids if ids.count(i) > 1}
    if dubbel:
        raise ValueError(f"Dubbele punt-id's in {REPORT}: {', '.join(sorted(dubbel))}.")
    return punten


def _normalize(item: Any, idx: int) -> dict[str, Any]:
    """Controleer één punt en zijn varianten."""
    if not isinstance(item, dict):
        raise ValueError(f"Punt {idx} in {REPORT} is geen object.")

    for veld in ("id", "punt"):
        if not str(item.get(veld) or "").strip():
            raise ValueError(f"Punt {idx} in {REPORT} mist {veld}.")

    opties = item.get("opties")
    if not isinstance(opties, list) or len(opties) < 2:
        raise ValueError(
            f"Punt {item['id']} in {REPORT} heeft minder dan twee varianten. Leg de "
            "keuze voor, geef geen advies."
        )

    genormaliseerd = []
    for optie in opties:
        if not isinstance(optie, dict):
            raise ValueError(f"Een variant van punt {item['id']} in {REPORT} is geen object.")
        for veld in ("key", "gevolg"):
            if not str(optie.get(veld) or "").strip():
                raise ValueError(
                    f"Een variant van punt {item['id']} in {REPORT} mist {veld}. Elke "
                    "variant noemt wat hij met de tekst doet."
                )
        genormaliseerd.append({
            "key": str(optie["key"]).strip(),
            "gevolg": str(optie["gevolg"]).strip(),
        })

    if not any(o["key"] == VERWERPEN for o in genormaliseerd):
        raise ValueError(
            f"Punt {item['id']} in {REPORT} biedt geen variant '{VERWERPEN}'. Verwerpen "
            "hoort bij elk punt een even zichtbare optie te zijn (ADR-010 §3.3)."
        )

    extra = {}
    for veld in ("wat_de_draft_nu_zegt", "wat_het_archief_zegt"):
        tekst = str(item.get(veld) or "").strip()
        if tekst:
            extra[veld] = tekst
    return {
        "id": str(item["id"]).strip(),
        "bron": str(item.get("bron") or "grok").strip(),
        "punt": str(item["punt"]).strip(),
        "raakt": str(item.get("raakt") or "sectie").strip(),
        "opties": genormaliseerd,
        **extra,
    }


def read_points(post_dir: str) -> list[dict[str, Any]]:
    """Lees de punten uit synthese.md op schijf."""
    pad = os.path.join(post_dir, REPORT)
    if not os.path.isfile(pad):
        raise FileNotFoundError(f"{REPORT} ontbreekt in {post_dir}.")
    with open(pad, encoding="utf-8") as f:
        return parse_points(f.read())


def open_points(state: dict[str, Any], punten: list[dict[str, Any]]) -> list[str]:
    """Geef de punt-id's waarover nog niet is beslist."""
    besluiten = state.get("synthese_besluiten") or {}
    return [p["id"] for p in punten if not (besluiten.get(p["id"]) or {}).get("keuze")]


def record_decision(
    state: dict[str, Any], punt: dict[str, Any], keuze: str, motivering: str, tijdstip: str
) -> None:
    """Leg de keuze van de auteur bij één punt vast."""
    geldig = [o["key"] for o in punt["opties"]]
    if keuze not in geldig:
        raise ValueError(f"Onbekende keuze '{keuze}' voor punt {punt['id']}. Kies uit: {', '.join(geldig)}.")
    state.setdefault("synthese_besluiten", {})[punt["id"]] = {
        "keuze": keuze,
        "motivering": (motivering or "").strip(),
        "at": tijdstip,
    }


def summarize(state: dict[str, Any], punten: list[dict[str, Any]]) -> dict[str, Any]:
    """Vat de stand van de synthese samen voor de CLI en de UI."""
    besluiten = state.get("synthese_besluiten") or {}
    regels = []
    for p in punten:
        besluit = besluiten.get(p["id"]) or {}
        regels.append({**p, "keuze": besluit.get("keuze"), "motivering": besluit.get("motivering")})
    verworpen = sum(1 for r in regels if r["keuze"] == VERWERPEN)
    return {
        "totaal": len(punten),
        "open": len(open_points(state, punten)),
        "verworpen": verworpen,
        "points": regels,
    }
