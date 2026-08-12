"""Agent brief generator voor de blogpost workflow."""

from __future__ import annotations

import os
import re
from typing import Any

from .constants import AGENT_FOR_PHASE


def agent_brief(phase: str, post_dir: str, state: dict[str, Any]) -> dict[str, Any]:
    """Genereer de gestructureerde agent_brief instructie voor een specifieke fase."""
    slug = state.get("slug") or os.path.basename(post_dir.rstrip("/"))
    rel = f"posts/{slug}"
    common = {
        "agent": AGENT_FOR_PHASE.get(phase),
        "phase": phase,
        "post_dir": rel,
        "slug": slug,
    }
    briefs = {
        "outline": {
            **common,
            "inputs": ["onderwerp/titel", "backlog of brainstorm indien genoemd"],
            "outputs": [f"{rel}/outline.md"],
            "instruction": (
                "Roep blogpost-onderzoeker aan. Schrijf een compacte outline met bronnen "
                f"(URL's geverifieerd) naar {rel}/outline.md. Verzin geen fase; alleen outline."
            ),
        },
        "draft": {
            **common,
            "inputs": [f"{rel}/outline.md", "reference/huisstijl.md"],
            "outputs": [f"{rel}/draft.md"],
            "instruction": (
                "Roep blogpost-schrijver aan. Schrijf draft.md in huisstijl op basis van outline.md. "
                "Geen feiten buiten de outline."
            ),
        },
        "style": {
            **common,
            "inputs": [f"{rel}/draft.md", "reference/huisstijl.md"],
            "outputs": ["rapport aan orkestrator/host (geen file verplicht)"],
            "instruction": (
                "Roep stijl-check aan op draft.md. Rapporteer alleen; pas de draft niet zelf aan. "
                "Leg het rapport vast in de gate-notitie bij approve/reject."
            ),
        },
        "series": {
            **common,
            "inputs": [f"{rel}/draft.md", "posts/*/"],
            "outputs": ["rapport aan orkestrator/host"],
            "instruction": (
                "Roep reeks-consistentie-check aan. Vergelijk met eerdere delen in posts/*/. "
                "Rapporteer alleen; pas de draft niet zelf aan."
            ),
        },
        "critique": {
            **common,
            "inputs": [f"{rel}/draft.md"],
            "outputs": [f"{rel}/grok-feedback.md"],
            "instruction": (
                "Roep grok-reviewer aan (Grok-MCP). Schrijf ruwe kritiek naar grok-feedback.md. "
                "Verzin geen kritiek als de tool faalt — laat complete falen."
            ),
        },
        "synthesis": {
            **common,
            "inputs": [f"{rel}/draft.md", f"{rel}/grok-feedback.md"],
            "outputs": [f"{rel}/synthese.md"],
            "instruction": (
                "Roep blogpost-onderzoeker aan voor synthese: weeg Grok-punten, schrijf "
                "aanpasvoorstel naar synthese.md. Herschrijf draft.md niet in deze stap."
            ),
        },
        "visuals": {
            **common,
            "inputs": [f"{rel}/draft.md", "reference/huisstijl.md"],
            "outputs": [f"{rel}/visuals/", "beeldrefs in draft.md"],
            "instruction": (
                "Roep blogpost-visuals aan. Spaarzame SVG's, render via scripts/render_svg.py, "
                "zet ![alt](visuals/....png) in draft.md."
            ),
        },
        "factcheck": {
            **common,
            "inputs": [f"{rel}/draft.md"],
            "outputs": [f"{rel}/feitencheck.md"],
            "instruction": (
                "Roep bron-check aan. Elk citaat en elke bron in draft.md tegen de bron "
                "leggen; niets aannemen op gezag van de outline. Rapport naar "
                f"{rel}/feitencheck.md. Dit is de laatste controle voor publicatie."
            ),
        },
        "deploy": {
            **common,
            "inputs": [f"{rel}/draft.md", f"{rel}/visuals/"],
            "outputs": ["WordPress concept (post_id, edit_url)"],
            "instruction": (
                "Alleen na deploy_approved. Roep blogpost-deploy / "
                f"python3 scripts/deploy_post.py --post-dir {rel} aan. "
                "Daarna: orchestrate.py complete deploy --post-id N --edit-url URL."
            ),
        },
    }
    return briefs.get(phase, {**common, "instruction": f"Voer phase {phase} uit."})
