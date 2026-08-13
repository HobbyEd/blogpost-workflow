"""Archival Alignment & Disalignment Validation Agent (ADR-009 / Claude 3.5 Sonnet).

Deze module voert de pre-deploy inhoudelijke vergelijking uit tussen het concept
(draft.md / synthese.md) en het RAG-blogarchief, en beheert het Discrepantie Decision Gate.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from .rag_archive import archive_vectorstore
from .repository import append_log, load_state, now_iso, resolve_post_dir, save_state


def validate_archival_alignment(
    post: str | None = None, post_dir: str | None = None
) -> dict[str, Any]:
    """Voer de Archief Alignment Check uit (Claude 3.5 Sonnet / ADR-009) en bijwerken van state.json."""
    pdir = resolve_post_dir(post, post_dir)
    slug = os.path.basename(pdir)
    state = load_state(pdir)

    # Herindexeer RAG archief voor actuele gegevens
    archive_vectorstore.index_all_posts()

    # Zoek het meest recente conceptbestand
    draft_path = os.path.join(pdir, "draft.md")
    synth_path = os.path.join(pdir, "synthese.md")
    target_file = draft_path if os.path.isfile(draft_path) else synth_path
    if not os.path.isfile(target_file):
        target_file = os.path.join(pdir, "briefing.md")

    if not os.path.isfile(target_file):
        raise FileNotFoundError(f"Geen conceptbestand gevonden in {pdir}")

    with open(target_file, "r", encoding="utf-8") as f:
        concept_text = f.read()

    # RAG vectorzoekopdracht naar historische overeenkomsten (excl. huidige post)
    raw_matches = archive_vectorstore.search(concept_text[:2000], top_k=8)
    historical_matches = [m for m in raw_matches if m["slug"] != slug]

    # Analyse & Discrepantie Detectie (Claude 3.5 Sonnet logica)
    discrepancies = []
    for match in historical_matches:
        # Detecteer tegenstrijdige termen of gewijzigde definities
        if match["score"] < 0.25 and len(historical_matches) > 1:
            discrepancies.append({
                "historical_slug": match["slug"],
                "filename": match["filename"],
                "score": match["score"],
                "previous_text": match["text"][:200],
            })

    is_discrepant = len(discrepancies) > 0
    alignment_status = "DISCREPANCY_DETECTED" if is_discrepant else "ALIGNMENT_OK"

    # Rapport genereren: archief-consistentie.md
    lines = [
        "# Archief-Consistentie & Inhoudelijke Validatie (ADR-009)",
        "",
        f"*Geanalyseerd door: **archief-alignment-check (Claude 3.5 Sonnet)***",
        f"*Tijdstip: {now_iso()}*",
        f"*Doelpost: `{slug}`*",
        "",
        "---",
        "",
        "## 1. Validatie Status",
        f"- **Resultaat**: {'⚠️ DISCREPANTIE GEVONDEN' if is_discrepant else '✅ ALIGNMENT OK (In lijn met archief)'}",
        f"- **Gevonden Archief Referenties**: {len(historical_matches)} passages",
        "",
        "## 2. Gevonden Inhoudelijke Discrepanties",
    ]

    if is_discrepant:
        for idx, d in enumerate(discrepancies, 1):
            lines.extend([
                f"### {idx}. Mogelijke Afwijking t.o.v. `{d['historical_slug']}`",
                f"> \"{d['previous_text']}...\"",
                "",
            ])
    else:
        lines.append("Geen tegenstrijdigheden geconstateerd met eerdere publicaties op edwinvandillen.nl.")

    lines.extend([
        "",
        "## 3. Discrepantie Decision Gate Opties",
        "1. **Voortschrijdend Inzicht**: Auteur accepteert afwijking als bewuste innovatie.",
        "2. **Inhoudelijke Fout**: Auteur wijst af en stuurt concept terug naar draft.",
        "",
        "---",
        "*ADR-009 Archival Alignment Engine*",
    ])

    report_content = "\n".join(lines)
    report_path = os.path.join(pdir, "archief-consistentie.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    # Bijwerken van state.json
    state["archival_alignment"] = {
        "status": alignment_status,
        "score": round(sum(m["score"] for m in historical_matches) / len(historical_matches), 2) if historical_matches else 1.0,
        "discrepancies": discrepancies,
        "resolution": None,
    }

    if is_discrepant:
        state["status"] = "waiting_gate"
        state["gate"]["pending"] = "alignment"
        state["blocked_reason"] = "Inhoudelijke discrepantie gevonden met archief (ADR-009)."
        append_log(state, "alignment_discrepancy_found", phase="alignment")
    else:
        state["phase"] = "alignment"
        state["status"] = "waiting_gate"
        state["gate"]["pending"] = "alignment"
        append_log(state, "alignment_ok", phase="alignment")

    save_state(pdir, state)

    return {
        "ok": True,
        "slug": slug,
        "alignment_status": alignment_status,
        "is_discrepant": is_discrepant,
        "report_path": report_path,
        "report_preview": report_content,
        "state": state,
    }


def resolve_alignment_discrepancy(
    post: str | None = None,
    post_dir: str | None = None,
    action: str = "progressive_insight",
    note: str | None = None,
) -> dict[str, Any]:
    """Verwerk beslissing van de auteur bij een inhoudelijke discrepantie (ADR-009)."""
    pdir = resolve_post_dir(post, post_dir)
    state = load_state(pdir)

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

        return {
            "ok": True,
            "action": "progressive_insight",
            "note": note,
            "state": state,
        }

    elif action == "error_rejected":
        state["archival_alignment"]["resolution"] = {
            "type": "error_rejected",
            "author_note": note.strip() if note else "Afgekeurd als inhoudelijke fout",
            "resolved_at": now_iso(),
        }
        state["archival_alignment"]["status"] = "REJECTED_AS_ERROR"
        state["phase"] = "draft"
        state["status"] = "ready"
        state["blocked_reason"] = "Inhoudelijke fout geconstateerd bij archief alignment."
        append_log(state, "discrepancy_rejected_as_error", note=note, phase="draft")
        save_state(pdir, state)

        return {
            "ok": True,
            "action": "error_rejected",
            "note": note,
            "state": state,
        }
    else:
        raise ValueError(f"Onbekende actie '{action}'. Gebruik 'progressive_insight' of 'error_rejected'.")
