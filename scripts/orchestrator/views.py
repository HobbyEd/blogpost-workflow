"""Welke artefacten de auteur in de detailweergave kan openen.

Eén inventaris, dezelfde als de control plane. De UI verzint geen tweede lijst.
"""

from __future__ import annotations

import os
from typing import Any

from .constants import (
    CONDITIONAL_GATES,
    FACTCHECK_PHASES,
    HARD_GATES,
    PHASE_LABELS,
    PHASE_VIEW_FILES,
    PHASES,
)
from .probes import file_nonempty

_IMAGE_EXT = {".png", ".svg", ".jpg", ".jpeg", ".webp"}


def list_visual_files(post_dir: str) -> list[dict[str, str]]:
    """Beeldbestanden in visuals/, één kaart per stam (png gaat voor svg)."""
    vdir = os.path.join(post_dir, "visuals")
    if not os.path.isdir(vdir):
        return []

    per_stam: dict[str, dict[str, str]] = {}
    for name in sorted(os.listdir(vdir)):
        if name.startswith("."):
            continue
        stam, ext = os.path.splitext(name)
        ext_l = ext.lower()
        if ext_l not in _IMAGE_EXT:
            continue
        pad = os.path.join(vdir, name)
        if not file_nonempty(pad):
            continue
        per_stam.setdefault(stam, {})[ext_l] = name

    items: list[dict[str, str]] = []
    for stam, files in per_stam.items():
        preview = files.get(".png") or files.get(".jpg") or files.get(".jpeg") or files.get(".webp") or files.get(".svg")
        if not preview:
            continue
        items.append(
            {
                "name": preview,
                "stem": stam,
                "path": f"visuals/{preview}",
            }
        )
    return items


def build_artefact_views(state: dict[str, Any], post_dir: str) -> list[dict[str, Any]]:
    """Per fase: welke bestanden er liggen en of de tab te openen is."""
    verdicts = state.get("verdicts") or {}
    views: list[dict[str, Any]] = []
    for phase in PHASES:
        if phase in {"intake", "deploy", "done"}:
            continue
        if phase == "visuals":
            files = list_visual_files(post_dir)
            views.append(
                {
                    "id": "visuals",
                    "phase": "visuals",
                    "label": "Visuals",
                    "kind": "visuals",
                    "present": bool(files),
                    "files": files,
                    "verdict": None,
                }
            )
            continue

        namen = PHASE_VIEW_FILES.get(phase) or ()
        if not namen:
            continue
        file_rows = [
            {"name": naam, "present": file_nonempty(os.path.join(post_dir, naam))}
            for naam in namen
        ]
        verdict = verdicts.get(phase)
        views.append(
            {
                "id": phase,
                "phase": phase,
                "label": _korte_label(phase),
                "kind": "markdown",
                "present": any(f["present"] for f in file_rows),
                "files": file_rows,
                "verdict": _verdict_samenvatting(verdict) if verdict else None,
            }
        )
    return views


def gate_reason(state: dict[str, Any]) -> dict[str, Any] | None:
    """Waarom de keten op waiting_gate staat, in mensentaal."""
    if state.get("status") != "waiting_gate":
        return None

    phase = (state.get("gate") or {}).get("pending") or state.get("phase")
    verdict = ((state.get("verdicts") or {}).get(phase) or {})
    blocking = int(verdict.get("blocking") or 0)
    advisory = int(verdict.get("advisory") or 0)
    blocking_rows = [
        {
            "categorie": f.get("categorie") or "",
            "waar": f.get("waar") or "",
            "wat": f.get("wat") or "",
        }
        for f in (verdict.get("findings") or [])
        if f.get("severity") == "blocking"
    ]

    if phase in FACTCHECK_PHASES and blocking:
        woord = "bevinding" if blocking == 1 else "bevindingen"
        return {
            "phase": phase,
            "kind": "blocking",
            "blocking": blocking,
            "advisory": advisory,
            "headline": f"Gestopt: {blocking} blokkerende {woord} in de feitencheck.",
            "detail": "De keten mag niet verder. Stuur de punten terug naar de draft.",
            "findings": blocking_rows,
        }

    if phase in CONDITIONAL_GATES and blocking:
        woord = "bevinding" if blocking == 1 else "bevindingen"
        return {
            "phase": phase,
            "kind": "blocking",
            "blocking": blocking,
            "advisory": advisory,
            "headline": f"Gestopt: {blocking} blokkerende {woord} in {_korte_label(phase).lower()}.",
            "detail": "YOLO slaat deze gate niet over: er is iets voor te leggen.",
            "findings": blocking_rows,
        }

    if phase in HARD_GATES:
        return {
            "phase": phase,
            "kind": "hard",
            "blocking": blocking,
            "advisory": advisory,
            "headline": f"Harde gate na {_korte_label(phase).lower()}: hier is een besluit van jou nodig.",
            "detail": None,
            "findings": blocking_rows,
        }

    return {
        "phase": phase,
        "kind": "soft",
        "blocking": blocking,
        "advisory": advisory,
        "headline": f"Gate na {_korte_label(phase).lower()}.",
        "detail": "Met YOLO zou deze stap vanzelf doorgaan.",
        "findings": blocking_rows,
    }


def _korte_label(phase: str) -> str:
    ruw = PHASE_LABELS.get(phase, phase)
    # "2b Stijl-controle" → "Stijl-controle"
    delen = ruw.split(" ", 1)
    return delen[1] if len(delen) == 2 and delen[0][:1].isdigit() else ruw


def _verdict_samenvatting(verdict: dict[str, Any]) -> dict[str, Any]:
    return {
        "blocking": int(verdict.get("blocking") or 0),
        "advisory": int(verdict.get("advisory") or 0),
        "status": verdict.get("status") or "",
    }
