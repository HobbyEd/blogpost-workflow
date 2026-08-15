"""File I/O en opslag van state.json voor de blogpost workflow."""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any, Iterable

from .constants import (
    FLAG_NAMES,
    PHASES,
    SCHEMA_VERSION,
    STATUSES,
)
from .probes import probe_artefacts


def repo_root() -> str:
    """Geef het absolute pad naar de repository root."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def posts_root() -> str:
    """Geef het absolute pad naar de posts directory."""
    env = os.environ.get("BLOGPOST_POSTS_DIR")
    if env:
        return os.path.abspath(env)
    return os.path.join(repo_root(), "posts")


def resolve_post_dir(post: str | None, post_dir: str | None) -> str:
    """Herleid de postmap op basis van slug of direct pad."""
    if post_dir:
        path = os.path.abspath(post_dir)
    elif post:
        path = os.path.join(posts_root(), post)
    else:
        raise ValueError("Geef --post <slug> of --post-dir <pad>.")
    return path


def state_path(post_dir: str) -> str:
    """Pad naar state.json binnen een postmap."""
    return os.path.join(post_dir, "state.json")


def draft_fingerprint(post_dir: str) -> str | None:
    """Vingerafdruk van draft.md, of None als die er niet is.

    Hiermee wordt `deploy_approved` aan een concrete tekst gekoppeld. Zonder die
    koppeling bleef een goedkeuring staan terwijl de draft daarna nog werd herschreven,
    en stopte de deploy-gate niets meer.
    """
    path = os.path.join(post_dir, "draft.md")
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def record_derivation(state: dict[str, Any], phase: str, post_dir: str) -> None:
    """Leg vast van welke draft het resultaat van deze fase is afgeleid (ADR-010 §3.5)."""
    state.setdefault("derived_from", {})[phase] = draft_fingerprint(post_dir)


def stale_phases(state: dict[str, Any], post_dir: str, phases: Iterable[str]) -> list[str]:
    """Geef de fases waarvan het rapport aantoonbaar bij een oudere draft hoort.

    Alleen fases met een vastgelegde vingerafdruk die afwijkt van de huidige draft. Een
    fase zonder vingerafdruk telt níet als verouderd: dat zijn posts van vóór deze
    registratie, en die zonder aanleiding blokkeren maakt de melding waardeloos. Voor dat
    geval is er `unrecorded_phases`, die alleen waarschuwt.
    """
    huidig = draft_fingerprint(post_dir)
    afgeleid = state.get("derived_from") or {}
    return [p for p in phases if afgeleid.get(p) is not None and afgeleid[p] != huidig]


def unrecorded_phases(state: dict[str, Any], phases: Iterable[str]) -> list[str]:
    """Geef de fases zonder vastgelegde vingerafdruk: niet te toetsen op actualiteit."""
    afgeleid = state.get("derived_from") or {}
    return [p for p in phases if afgeleid.get(p) is None]


def now_iso() -> str:
    """Geef huidige UTC tijdstempel in ISO format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today() -> str:
    """Geef huidige datum in ISO format (YYYY-MM-DD)."""
    return date.today().isoformat()


def load_state(post_dir: str) -> dict[str, Any]:
    """Laad en normaliseer state.json uit een postmap."""
    path = state_path(post_dir)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Geen state.json in {post_dir}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return normalize_state(data)


def save_state(post_dir: str, state: dict[str, Any]) -> None:
    """Sla state.json atomair op via een tijdelijk bestand."""
    path = state_path(post_dir)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def append_log(
    state: dict[str, Any],
    event: str,
    note: str | None = None,
    phase: str | None = None,
) -> None:
    """Voeg een gebeurtenis toe aan het logboek in state.json."""
    entry: dict[str, Any] = {"at": now_iso(), "event": event}
    if phase is not None:
        entry["phase"] = phase
    elif state.get("phase"):
        entry["phase"] = state["phase"]
    if note:
        entry["note"] = note
    state.setdefault("log", []).append(entry)


def empty_state(slug: str, titel: str, yolo: bool = False) -> dict[str, Any]:
    """Genereer de initiële lege state dictionary voor een nieuwe post."""
    return {
        "schema_version": SCHEMA_VERSION,
        "slug": slug,
        "titel": titel,
        "aangemaakt": today(),
        "yolo_mode": bool(yolo),
        "phase": "outline",
        "status": "ready",
        "artefacts": {
            "outline": "missing",
            "draft": "missing",
            "stijlcheck": "missing",
            "leesbaarheid": "missing",
            "reeks_check": "missing",
            "grok_feedback": "missing",
            "synthese": "missing",
            "visuals": "missing",
            "factcheck": "missing",
            "alignment": "missing",
            "wp_post_id": None,
            "edit_url": None,
        },
        "flags": {
            "skip_synthesis": False,
            "skip_factcheck": False,
            "defer_critique": False,
            "deploy_approved": False,
        },
        "gate": {"pending": None, "last_decision": None},
        # Waaraan de deploy-goedkeuring hangt: de vingerafdruk van de draft die is
        # goedgekeurd. Wijkt draft.md daarna af, dan vervalt de goedkeuring.
        "deploy_approval": None,
        # Van welke draft het resultaat van elke controlefase is afgeleid (ADR-010 §3.5).
        "derived_from": {},
        # Uitkomst per controlefase: hoeveel blokkerend, hoeveel ter overweging.
        "verdicts": {},
        "blocked_reason": None,
        "log": [
            {
                "at": now_iso(),
                "event": "intake_completed",
                "phase": "intake",
                "note": "map en state.json aangemaakt",
            }
        ],
    }


def normalize_state(data: dict[str, Any]) -> dict[str, Any]:
    """Vul ontbrekende defaults aan in een geladen state dict."""
    base = empty_state(data.get("slug") or "unknown", data.get("titel") or "")
    out = deepcopy(base)
    out.update({k: data[k] for k in data if k not in ("artefacts", "flags", "gate", "log")})
    out["artefacts"] = {**base["artefacts"], **(data.get("artefacts") or {})}
    out["flags"] = {**base["flags"], **(data.get("flags") or {})}
    out["gate"] = {**base["gate"], **(data.get("gate") or {})}
    out["log"] = list(data.get("log") or base["log"])
    out["yolo_mode"] = bool(out.get("yolo_mode"))
    for k in FLAG_NAMES:
        out["flags"][k] = bool(out["flags"].get(k))
    if out.get("phase") not in PHASES:
        raise ValueError(f"Ongeldige phase: {out.get('phase')}")
    if out.get("status") not in STATUSES:
        raise ValueError(f"Ongeldige status: {out.get('status')}")
    return out


def sync_artefact_flags(state: dict[str, Any], post_dir: str) -> None:
    """Synchroniseer de aanwezigheid van bestanden op schijf naar state.json."""
    probed = probe_artefacts(post_dir)
    for k, v in probed.items():
        state["artefacts"][k] = v
