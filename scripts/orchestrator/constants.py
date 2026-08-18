"""Constants en domein-definities voor de blogpost workflow."""

from __future__ import annotations

SCHEMA_VERSION = 1

PHASES = [
    "intake",
    "outline",
    "draft",
    "factcheck_draft",
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
    "factcheck_draft",
    "style",
    "series",
    "critique",
    "synthesis",
    "visuals",
    "factcheck",
    "alignment",
    "deploy",
}

# Twee feitenchecks: direct na de draft, en opnieuw vóór alignment/deploy.
FACTCHECK_PHASES = frozenset({"factcheck_draft", "factcheck"})

# Soft gates may auto-approve when yolo_mode is on.
SOFT_GATES = {
    "outline",
    "draft",
    "style",
    "series",
    "critique",
    "visuals",
}

# Gates waar de auteur dezelfde fase mag terugsturen met een verplichte opmerking.
# Eerst alleen outline (Richten). Andere waiting_gates blijven approve/reject.
RETURN_ALLOWED_PHASES = frozenset({"outline"})
# Alleen de gates waar werkelijk iets te kiezen valt. De controlefases staan hier
# bewust niet in: die zijn **voorwaardelijk** hard (CONDITIONAL_GATES, ADR-010 §3.1).
# Zonder blokkerende bevinding schuiven ze door, met een bevinding stoppen ze ook in
# yolo_mode. Die afweging zit in engine.gate_type(), dat de state nodig heeft.
HARD_GATES = {"synthesis", "deploy", "intake"}

STATUSES = {"ready", "running", "waiting_gate", "blocked", "done"}

ARTEFACT_FILES = {
    "outline": "outline.md",
    "draft": "draft.md",
    "stijlcheck": "stijlcheck.md",
    "leesbaarheid": "leesbaarheid.md",
    "reeks_check": "reeks-check.md",
    "grok_feedback": "grok-feedback.md",
    "synthese": "synthese.md",
    "factcheck_draft": "feitencheck-draft.md",
    "factcheck": "feitencheck.md",
    "alignment": "archief-consistentie.md",
}

FLAG_NAMES = ("skip_synthesis", "defer_critique", "skip_factcheck", "deploy_approved")

# Fases waarvan het resultaat uit draft.md is afgeleid: wijzigt de draft, dan is hun
# rapport verouderd (ADR-010 §3.5). Bij het afronden van deze fases wordt de
# vingerafdruk van de draft vastgelegd in state.derived_from.
PHASES_DERIVED_FROM_DRAFT = ("factcheck_draft", "style", "series", "factcheck", "alignment")

# Welke daarvan een deploy tegenhouden zolang ze verouderd zijn. De stijl- en
# reeksrapporten worden wel bijgehouden maar blokkeren nog niet; die stap komt bij het
# bundelen van de bevindingen (ADR-010 §6, stap 2 en 3).
DEPLOY_REQUIRES_FRESH = ("factcheck_draft", "factcheck", "alignment")

# grok-feedback.md staat hier bewust niet bij. Een tweede kritiekronde is een keuze van
# de auteur, niet iets wat een tekstwijziging afdwingt (ADR-010 §3.2).

# Welke rapporten een controlefase oplevert. Elk rapport opent met een json-blok met
# bevindingen, zodat de gate zelf kan vaststellen of er iets voor te leggen is.
PHASE_REPORTS = {
    "style": ("stijlcheck.md", "leesbaarheid.md"),
    "series": ("reeks-check.md",),
    "factcheck_draft": ("feitencheck-draft.md",),
    "factcheck": ("feitencheck.md",),
    # alignment houdt het verdictformaat uit ADR-007 en staat hier niet bij.
}

# Bestanden die de detailweergave per fase toont. Visuals is een map, geen markdown.
PHASE_VIEW_FILES = {
    "outline": (ARTEFACT_FILES["outline"],),
    "draft": (ARTEFACT_FILES["draft"],),
    "style": PHASE_REPORTS["style"],
    "series": PHASE_REPORTS["series"],
    "critique": (ARTEFACT_FILES["grok_feedback"],),
    "synthesis": (ARTEFACT_FILES["synthese"],),
    "factcheck_draft": PHASE_REPORTS["factcheck_draft"],
    "factcheck": PHASE_REPORTS["factcheck"],
    "alignment": (ARTEFACT_FILES["alignment"],),
}

# Fases waarvan de gate alleen stopt bij een blokkerende bevinding (ADR-010 §3.1). De
# overige gates blijven onvoorwaardelijk: intake en outline zijn de Richten-gate, deploy
# is de Oordelen-gate, en synthesis is het beslismoment over de kritiekpunten.
CONDITIONAL_GATES = ("factcheck_draft", "style", "series", "factcheck", "alignment")

# De drie blokken uit ADR-010 §3.1, als groepering over de bestaande fasevolgorde. Het
# blok zegt wat voor soort beslissing er aan het eind valt:
#
#   Richten  — jouw beslissing over onderwerp, invalshoek en bronnen. Goedkoop te
#              corrigeren; na de draft kost dezelfde correctie uren.
#   Bouwen   — produceren en controleren. De gates hier stoppen alleen bij een
#              blokkerende bevinding (CONDITIONAL_GATES).
#   Oordelen — lezen in WordPress en beslissen. Live zetten valt buiten het systeem.
#
# `synthesis` hoort volgens ADR-010 in Oordelen, maar staat in de fasevolgorde nog vóór
# visuals. Verplaatsen is stap 5 uit §6; tot die tijd valt hij hier onder Bouwen, zodat de
# blokken aaneengesloten blijven en de stepper niet heen en weer springt.
BLOCKS = (
    ("richten", "Richten", ("intake", "outline")),
    ("bouwen", "Bouwen", ("draft", "factcheck_draft", "style", "series", "critique",
                          "synthesis", "visuals", "factcheck", "alignment")),
    ("oordelen", "Oordelen", ("deploy", "done")),
)

BLOCK_FOR_PHASE = {phase: key for key, _label, phases in BLOCKS for phase in phases}
BLOCK_LABELS = {key: label for key, label, _phases in BLOCKS}


# Welke artefact-sleutel (uit ARTEFACT_FILES / probe_artefacts) hoort bij welke
# fase, voor de statustabel. None = geen eigen artefact (rapport-only fases).
PHASE_ARTEFACT_KEY = {
    "intake": None,
    "outline": "outline",
    "draft": "draft",
    "factcheck_draft": "factcheck_draft",
    # style levert twee rapporten (stijlcheck.md en leesbaarheid.md); de tabel toont er
    # één, de postcheck eist ze allebei.
    "style": "stijlcheck",
    "series": "reeks_check",
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
    "factcheck_draft": "bron-check",
    "style": "stijl-check",
    "series": "reeks-consistentie-check",
    "critique": "grok-reviewer",
    "synthesis": "blogpost-onderzoeker",
    "visuals": "blogpost-visuals",
    "factcheck": "bron-check",
    "alignment": "archief-consistentie-check",
    "deploy": "blogpost-deploy",
}

PHASE_LABELS = {
    "intake": "0 Intake",
    "outline": "1 Outline en verrijking",
    "draft": "2 Draft schrijven",
    "factcheck_draft": "2a Bron- en feitencontrole",
    "style": "2b Stijl-controle",
    "series": "2c Reeks-consistentie",
    "critique": "3 Kritiek (Grok)",
    "synthesis": "4 Synthese",
    "visuals": "5 Visuals",
    "factcheck": "5b Feiten herkeuring",
    "alignment": "5c Archief-consistentie",
    "deploy": "6 Deploy (concept)",
    "done": "Klaar",
}

# Huisstijl-eis: elke post krijgt minimaal twee visuals.
MIN_VISUALS = 2
