"""Constants en domein-definities voor de blogpost workflow."""

from __future__ import annotations

SCHEMA_VERSION = 1

PHASES = [
    "intake",
    "outline",
    "draft",
    "style",
    "series",
    "critique",
    "synthesis",
    "visuals",
    "factcheck",
    "alignment",
    "deploy",
    "done",
]

# Content phases that produce work (run/complete).
RUNNABLE = {
    "outline",
    "draft",
    "style",
    "series",
    "critique",
    "synthesis",
    "visuals",
    "factcheck",
    "alignment",
    "deploy",
}

# Soft gates may auto-approve when yolo_mode is on.
SOFT_GATES = {
    "outline",
    "draft",
    "style",
    "series",
    "critique",
    "visuals",
}
HARD_GATES = {"synthesis", "factcheck", "alignment", "deploy", "intake"}

STATUSES = {"ready", "running", "waiting_gate", "blocked", "done"}

ARTEFACT_FILES = {
    "outline": "outline.md",
    "draft": "draft.md",
    "grok_feedback": "grok-feedback.md",
    "synthese": "synthese.md",
    "factcheck": "feitencheck.md",
    "alignment": "archief-consistentie.md",
}

FLAG_NAMES = ("skip_synthesis", "defer_critique", "skip_factcheck", "deploy_approved")

# Welke artefact-sleutel (uit ARTEFACT_FILES / probe_artefacts) hoort bij welke
# fase, voor de statustabel. None = geen eigen artefact (rapport-only fases).
PHASE_ARTEFACT_KEY = {
    "intake": None,
    "outline": "outline",
    "draft": "draft",
    "style": None,
    "series": None,
    "critique": "grok_feedback",
    "synthesis": "synthese",
    "visuals": "visuals",
    "factcheck": "factcheck",
    "alignment": "alignment",
    "deploy": "deploy",
    "done": None,
}

AGENT_FOR_PHASE = {
    "outline": "blogpost-onderzoeker",
    "draft": "blogpost-schrijver",
    "style": "stijl-check",
    "series": "reeks-consistentie-check",
    "critique": "grok-reviewer",
    "synthesis": "blogpost-onderzoeker",
    "visuals": "blogpost-visuals",
    "factcheck": "bron-check",
    "alignment": "archief-alignment-check",
    "deploy": "blogpost-deploy",
}

PHASE_LABELS = {
    "intake": "0 Intake",
    "outline": "1 Outline en verrijking",
    "draft": "2 Draft schrijven",
    "style": "2b Stijl-controle",
    "series": "2c Reeks-consistentie",
    "critique": "3 Kritiek (Grok)",
    "synthesis": "4 Synthese",
    "visuals": "5 Visuals",
    "factcheck": "5b Bron- en feitencontrole",
    "alignment": "5c Archief Alignment (Sonnet)",
    "deploy": "6 Deploy (concept)",
    "done": "Klaar",
}

# Huisstijl-eis: elke post krijgt minimaal twee visuals.
MIN_VISUALS = 2
