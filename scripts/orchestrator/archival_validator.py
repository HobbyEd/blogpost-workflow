"""Archief-consistentie: verdict inlezen en het discrepantie-gate beheren (ADR-007).

De inhoudelijke vergelijking zelf gebeurt **niet hier**. Die doet de subagent
`archief-consistentie-check` in fase 5c, net als de stijl-check en de bron-check: hij
bevraagt de RAG-index, beoordeelt, en schrijft `archief-consistentie.md`.

Deze module leest het verdict uit dat rapport en vertaalt het naar `state.json`. Ze
beoordeelt niets zelf. Een eerdere versie deed dat wel, met `if match["score"] < 0.25`,
en die logica stond omgekeerd: een lage gelijkenisscore betekent dat een passage weinig
met het stuk te maken heeft, niet dat hij het tegenspreekt.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from .repository import append_log, load_state, now_iso, resolve_post_dir, save_state

REPORT_FILE = "archief-consistentie.md"

ALIGNMENT_OK = "ALIGNMENT_OK"
DISCREPANCY_DETECTED = "DISCREPANCY_DETECTED"
VALID_STATUSES = {ALIGNMENT_OK, DISCREPANCY_DETECTED}

#: Velden die elke bevinding moet hebben. `previous_text` en `current_text` samen zijn
#: het geciteerde paar uit ADR-007: zonder beide citaten is er geen bevinding.
REQUIRED_DISCREPANCY_FIELDS = ("historical_slug", "previous_text", "current_text")

_JSON_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.S)


def report_path(post_dir: str) -> str:
    """Pad naar het rapport van de archief-consistentie-check."""
    return os.path.join(post_dir, REPORT_FILE)


def parse_alignment_report(text: str) -> dict[str, Any]:
    """Lees het machineleesbare verdict uit de tekst van het rapport.

    Het rapport begint met een ```json-blok. De prozatekst eronder is voor de mens;
    dit blok is voor de state machine. Gooit ValueError als het blok ontbreekt, niet
    parseert, of niet aan ADR-007 voldoet.
    """
    match = _JSON_FENCE.search(text)
    if not match:
        raise ValueError(
            f"{REPORT_FILE} bevat geen ```json-verdictblok. De agent moet het rapport "
            "openen met een json-blok met 'status' en 'discrepancies'."
        )
    try:
        verdict = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Het verdictblok in {REPORT_FILE} is geen geldige JSON: {e}") from None

    if not isinstance(verdict, dict):
        raise ValueError(f"Het verdictblok in {REPORT_FILE} moet een object zijn.")

    status = verdict.get("status")
    if status not in VALID_STATUSES:
        raise ValueError(
            f"Onbekende status '{status}' in {REPORT_FILE}. "
            f"Gebruik {ALIGNMENT_OK} of {DISCREPANCY_DETECTED}."
        )

    raw = verdict.get("discrepancies") or []
    if not isinstance(raw, list):
        raise ValueError(f"'discrepancies' in {REPORT_FILE} moet een lijst zijn.")

    discrepancies = [_normalize_discrepancy(d, idx) for idx, d in enumerate(raw, 1)]

    if status == DISCREPANCY_DETECTED and not discrepancies:
        raise ValueError(
            f"{DISCREPANCY_DETECTED} zonder bevindingen in {REPORT_FILE}. "
            "Een gate die afgaat zonder geciteerd paar wordt weggeklikt (ADR-007)."
        )
    if status == ALIGNMENT_OK and discrepancies:
        raise ValueError(
            f"{ALIGNMENT_OK} met {len(discrepancies)} bevinding(en) in {REPORT_FILE}. "
            "Kies één van beide."
        )

    return {"status": status, "discrepancies": discrepancies}


def _normalize_discrepancy(item: Any, idx: int) -> dict[str, Any]:
    """Controleer één bevinding op het geciteerde paar en normaliseer de velden."""
    if not isinstance(item, dict):
        raise ValueError(f"Bevinding {idx} in {REPORT_FILE} is geen object.")

    missing = [f for f in REQUIRED_DISCREPANCY_FIELDS if not str(item.get(f) or "").strip()]
    if missing:
        raise ValueError(
            f"Bevinding {idx} in {REPORT_FILE} mist {', '.join(missing)}. ADR-007 eist bij "
            "elke bevinding beide citaten: de zin uit het concept en de zin uit de "
            "eerdere post. Kan de agent die niet geven, dan is er geen bevinding."
        )

    return {
        "historical_slug": str(item["historical_slug"]).strip(),
        "historical_ref": str(item.get("historical_ref") or "").strip() or None,
        "previous_text": str(item["previous_text"]).strip(),
        "current_text": str(item["current_text"]).strip(),
        "toelichting": str(item.get("toelichting") or "").strip() or None,
    }


def read_alignment_verdict(post_dir: str) -> dict[str, Any]:
    """Lees en valideer het verdict uit het rapport op schijf."""
    path = report_path(post_dir)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"{REPORT_FILE} ontbreekt in {post_dir}. Draai eerst de fase alignment: de "
            "subagent archief-consistentie-check schrijft dit rapport."
        )
    with open(path, encoding="utf-8") as f:
        return parse_alignment_report(f.read())


def apply_alignment_verdict(state: dict[str, Any], verdict: dict[str, Any]) -> bool:
    """Zet het verdict in state.json. Geeft terug of er een discrepantie is.

    Raakt phase en status niet aan; dat doet de gate-logica in engine.py.
    """
    state["archival_alignment"] = {
        "status": verdict["status"],
        "discrepancies": verdict["discrepancies"],
        "resolution": None,
        "checked_at": now_iso(),
    }
    return verdict["status"] == DISCREPANCY_DETECTED


def is_discrepant(state: dict[str, Any]) -> bool:
    """True zolang een gevonden discrepantie nog niet door de auteur is afgehandeld."""
    return (state.get("archival_alignment") or {}).get("status") == DISCREPANCY_DETECTED


def ingest_alignment_report(
    post: str | None = None, post_dir: str | None = None
) -> dict[str, Any]:
    """Lees het rapport in en werk state.json bij, zonder de fase te verschuiven.

    Idempotent: bedoeld voor de Web UI om het verdict te verversen. De fase-overgang
    loopt via de normale `complete alignment` in de service.
    """
    pdir = resolve_post_dir(post, post_dir)
    state = load_state(pdir)
    verdict = read_alignment_verdict(pdir)
    discrepant = apply_alignment_verdict(state, verdict)
    append_log(
        state,
        "alignment_discrepancy_found" if discrepant else "alignment_ok",
        note=f"{len(verdict['discrepancies'])} bevinding(en)" if discrepant else None,
        phase="alignment",
    )
    save_state(pdir, state)

    with open(report_path(pdir), encoding="utf-8") as f:
        report_content = f.read()

    return {
        "ok": True,
        "slug": state["slug"],
        "alignment_status": verdict["status"],
        "is_discrepant": discrepant,
        "report_path": report_path(pdir),
        "report_preview": report_content,
        "state": state,
    }


def resolve_alignment_discrepancy(
    post: str | None = None,
    post_dir: str | None = None,
    action: str = "progressive_insight",
    note: str | None = None,
) -> dict[str, Any]:
    """Verwerk de beslissing van de auteur bij een gevonden discrepantie (ADR-007)."""
    pdir = resolve_post_dir(post, post_dir)
    state = load_state(pdir)

    if not state.get("archival_alignment"):
        raise ValueError(
            "Er is geen archief-consistentie-verdict om af te handelen. Draai eerst de "
            "fase alignment."
        )

    if action == "progressive_insight":
        if not note or not note.strip():
            raise ValueError("Een toelichtingsnotitie is verplicht bij voortschrijdend inzicht.")

        state["archival_alignment"]["resolution"] = {
            "type": "progressive_insight",
            "author_note": note.strip(),
            "resolved_at": now_iso(),
        }
        state["archival_alignment"]["status"] = "RESOLVED_PROGRESSIVE_INSIGHT"
        state["phase"] = "alignment"
        state["status"] = "waiting_gate"
        state["gate"]["pending"] = "alignment"
        state["blocked_reason"] = None
        append_log(state, "discrepancy_resolved_progressive_insight", note=note, phase="alignment")
        save_state(pdir, state)

        return {"ok": True, "action": "progressive_insight", "note": note, "state": state}

    if action == "error_rejected":
        state["archival_alignment"]["resolution"] = {
            "type": "error_rejected",
            "author_note": note.strip() if note else "Afgekeurd als inhoudelijke fout",
            "resolved_at": now_iso(),
        }
        state["archival_alignment"]["status"] = "REJECTED_AS_ERROR"
        state["phase"] = "draft"
        state["status"] = "ready"
        state["gate"]["pending"] = None
        # Geen blocked_reason: de status is 'ready', niet 'blocked'. De reden staat in
        # het logboek en in archival_alignment.resolution.
        state["blocked_reason"] = None
        append_log(
            state,
            "discrepancy_rejected_as_error",
            note=note or "Inhoudelijke fout geconstateerd bij archief-consistentie.",
            phase="draft",
        )
        save_state(pdir, state)

        return {"ok": True, "action": "error_rejected", "note": note, "state": state}

    raise ValueError(f"Onbekende actie '{action}'. Gebruik 'progressive_insight' of 'error_rejected'.")
