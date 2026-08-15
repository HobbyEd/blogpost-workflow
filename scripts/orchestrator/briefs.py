"""Agent brief generator voor de blogpost workflow."""

from __future__ import annotations

import os
import re
from typing import Any

from .constants import AGENT_FOR_PHASE


def rag_search_step(onderwerp: str, top_k: int = 12) -> str:
    """De verplichte openingsstap: eerst het eigen archief bevragen (ADR-006).

    Zonder deze stap keek de keten alleen naar de twintig nieuwste posts van de live
    site, waardoor ouder materiaal structureel onzichtbaar bleef.
    """
    return (
        f'VERPLICHTE EERSTE STAP: python3 scripts/rag_cli.py search "{onderwerp}" '
        f"--top-k {top_k}. Herhaal met varianten op de kernbegrippen; retrieval is "
        "lexicaal (TF-IDF), dus andere woorden voor hetzelfde idee vindt hij niet. "
        "Lees daarnaast reference/corpus-inventaris.md als vangnet. "
        "Faalt de index, meld dat bij de gate en verzin geen eerdere posts."
    )


def agent_brief(phase: str, post_dir: str, state: dict[str, Any]) -> dict[str, Any]:
    """Genereer de gestructureerde agent_brief instructie voor een specifieke fase."""
    slug = state.get("slug") or os.path.basename(post_dir.rstrip("/"))
    rel = f"posts/{slug}"
    onderwerp = state.get("titel") or slug
    common = {
        "agent": AGENT_FOR_PHASE.get(phase),
        "phase": phase,
        "post_dir": rel,
        "slug": slug,
    }
    briefs = {
        "outline": {
            **common,
            "inputs": [
                "onderwerp/titel",
                "backlog of brainstorm indien genoemd",
                "RAG-archief (scripts/rag_cli.py search)",
                "reference/corpus-inventaris.md",
            ],
            "outputs": [f"{rel}/outline.md"],
            "instruction": (
                f"{rag_search_step(onderwerp)} "
                "Roep daarna blogpost-onderzoeker aan en geef de treffers mee. Schrijf een "
                "compacte outline met bronnen (URL's geverifieerd) naar "
                f"{rel}/outline.md. Verzin geen fase; alleen outline."
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
            "outputs": [f"{rel}/stijlcheck.md", f"{rel}/leesbaarheid.md"],
            "instruction": (
                "Roep stijl-check én leesbaarheid-check aan op draft.md; ze draaien altijd "
                f"samen. De stijl-check schrijft {rel}/stijlcheck.md, de leesbaarheid-check "
                f"{rel}/leesbaarheid.md. Beide rapporteren alleen en passen draft.md niet aan; "
                "corrigeren doe jij ná Edwins akkoord. Draai je deze fase opnieuw (de "
                "verplichte herkeuring na de synthese), laat de agents dan een nieuwe "
                "gedateerde ronde toevoegen in plaats van het bestand te overschrijven."
            ),
        },
        "series": {
            **common,
            "inputs": [
                f"{rel}/draft.md",
                "posts/*/",
                "RAG-archief (scripts/rag_cli.py search)",
                "reference/corpus-inventaris.md",
            ],
            "outputs": [f"{rel}/reeks-check.md"],
            "instruction": (
                f"{rag_search_step(onderwerp)} "
                "Zoek ook op de kernbegrippen uit de draft zelf, om te vinden waar die "
                "begrippen eerder anders zijn genoemd. Roep daarna "
                "reeks-consistentie-check aan en geef de treffers mee; die agent heeft "
                "zelf geen Bash. Vergelijk met eerdere delen in posts/*/. Het rapport "
                f"gaat naar {rel}/reeks-check.md, ook als er geen eerdere delen zijn: "
                "leg dan vast dát er niets te vergelijken viel. Rapporteer alleen; pas "
                "de draft niet zelf aan."
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
            "inputs": [
                f"{rel}/draft.md",
                f"{rel}/grok-feedback.md",
                "RAG-archief (scripts/rag_cli.py search)",
            ],
            "outputs": [f"{rel}/synthese.md"],
            "instruction": (
                "Roep blogpost-onderzoeker aan voor synthese: weeg Grok-punten, schrijf "
                "aanpasvoorstel naar synthese.md. Herschrijf draft.md niet in deze stap."
            ),
        },
                f"{rag_search_step(onderwerp)} Zo weeg je Grok-kritiek tegen wat Edwin "
                "hier eerder over schreef, niet alleen tegen de draft. "
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
        "alignment": {
            **common,
            "inputs": [
                f"{rel}/draft.md",
                "RAG-archief (scripts/rag_cli.py search)",
                "reference/corpus-inventaris.md",
            ],
            "outputs": [f"{rel}/archief-consistentie.md"],
            "instruction": (
                "Roep archief-consistentie-check aan. Leg de definitieve draft naast het "
                "hele archief en zoek inhoudelijke tegenspraak met eerder gepubliceerd "
                f"werk. {rag_search_step(onderwerp)} Zoek per kernstelling apart, niet "
                "één keer op het onderwerp. Meld een bevinding alleen met beide citaten: "
                "de zin uit het concept en de zin uit de eerdere post; zonder dat paar "
                "weigert complete het rapport. Schrijf "
                f"{rel}/archief-consistentie.md, beginnend met het json-verdictblok "
                "(status ALIGNMENT_OK of DISCREPANCY_DETECTED). Pas draft.md niet aan."
            ),
        },
            "instruction": (
                "Alleen na deploy_approved. Roep blogpost-deploy / "
                f"python3 scripts/deploy_post.py --post-dir {rel} aan. "
                "Daarna: orchestrate.py complete deploy --post-id N --edit-url URL."
            ),
        },
    }
    return briefs.get(phase, {**common, "instruction": f"Voer phase {phase} uit."})
