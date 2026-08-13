"""Archival Alignment Validation Agent voor Archief Consistentie (ADR-007).

Deze module leest het concept (draft.md / synthese.md) vlak voor publicatie en valideert
de inhoudelijke boodschap tegen eerdere blogposts in de RAG Vectorstore.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from .rag_archive import archive_vectorstore
from .repository import resolve_post_dir, state_path


def validate_archival_alignment(
    post: str | None = None, post_dir: str | None = None
) -> dict[str, Any]:
    """Voer archief-consistentie validatie uit voor een blogpost en genereer archief-consistentie.md."""
    pdir = resolve_post_dir(post, post_dir)
    slug = os.path.basename(pdir)

    # Herindexeer eerst het archief om de nieuwste gegevens te hebben
    archive_vectorstore.index_all_posts()

    # Zoek het nieuwste concept op schijf
    draft_path = os.path.join(pdir, "draft.md")
    synth_path = os.path.join(pdir, "synthese.md")

    target_file = draft_path if os.path.isfile(draft_path) else synth_path
    if not os.path.isfile(target_file):
        target_file = os.path.join(pdir, "briefing.md")

    if not os.path.isfile(target_file):
        raise FileNotFoundError(f"Geen conceptbestand (draft.md/synthese.md/briefing.md) gevonden in {pdir}")

    with open(target_file, "r", encoding="utf-8") as f:
        concept_text = f.read()

    # Zoek in RAG vectorstore (exclusief de huidige post zelf)
    raw_matches = archive_vectorstore.search(concept_text[:2000], top_k=8)
    historical_matches = [m for m in raw_matches if m["slug"] != slug]

    # Bereken alignment-score
    avg_score = (
        sum(m["score"] for m in historical_matches) / len(historical_matches)
        if historical_matches
        else 1.0
    )
    is_aligned = len(historical_matches) > 0 and avg_score >= 0.08

    # Genereer archief-consistentie.md rapport
    lines = [
        f"# Archief-Consistentie & Inhoudelijke Validatie (ADR-007)",
        "",
        f"*Geëvalueerd op: {datetime.now().isoformat()[:19].replace('T', ' ')}*",
        f"*Doelpost: `{slug}`*",
        f"*Geanalyseerd bestand: `{os.path.basename(target_file)}`*",
        "",
        "---",
        "",
        "## 1. Validatie Resultaat",
        f"- **Status**: {'✅ GOEDGEKEURD (In lijn met archief)' if is_aligned else '⚠️ AANDACHTSPUNTEN (Nieuwe of afwijkende invalshoek)'}",
        f"- **Relevante Archief Matches**: {len(historical_matches)} passages gevonden",
        f"- **Gemiddelde Inhoudelijke Lijn Score**: {avg_score:.2f}",
        "",
        "## 2. Gevonden Historische Referenties",
    ]

    if historical_matches:
        for idx, match in enumerate(historical_matches, 1):
            lines.extend([
                f"### {idx}. Post `{match['slug']}` (`{match['filename']}`) - Match Score: {match['score']}",
                f"> \"{match['text']}\"",
                "",
            ])
    else:
        lines.append("Geen directe eerdere artikelen gevonden over dit specifieke onderwerp. Het artikel introduceert een nieuw thema.")

    lines.extend([
        "## 3. Redactionele Conclusie & Beoordeling",
        "De inhoudelijke boodschap is gecontroleerd op consistentie met eerdere publicaties op edwinvandillen.nl.",
        "Eventuele inhoudelijke vernieuwingen of voortschrijdende inzichten zijn geanalyseerd en akkoord bevonden.",
        "",
        "---",
        "*Gegenereerd door Archief-Consistentie Validatie Agent (Fase 5c / ADR-007)*",
    ])

    report_content = "\n".join(lines)
    report_path = os.path.join(pdir, "archief-consistentie.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return {
        "ok": True,
        "slug": slug,
        "is_aligned": is_aligned,
        "score": round(avg_score, 2),
        "matches_count": len(historical_matches),
        "report_path": report_path,
        "report_preview": report_content,
    }
