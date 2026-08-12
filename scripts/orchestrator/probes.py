"""Bestandscontrole en artefact probes voor de blogpost workflow."""

from __future__ import annotations

import os
import re
from typing import Any

from .constants import ARTEFACT_FILES, MIN_VISUALS

IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def file_nonempty(path: str) -> bool:
    """Controleer of een bestand bestaat en niet leeg is (>0 bytes)."""
    return os.path.isfile(path) and os.path.getsize(path) > 0


def count_local_visuals(post_dir: str) -> int:
    """Tel bruikbare beeldbestanden in visuals/.

    SVG en PNG van dezelfde visual tellen als een: de PNG is enkel de render voor
    WordPress, geen tweede visual.
    """
    vdir = os.path.join(post_dir, "visuals")
    if not os.path.isdir(vdir):
        return 0
    stammen = set()
    for name in os.listdir(vdir):
        if name.startswith("."):
            continue
        stam, ext = os.path.splitext(name)
        if ext.lower() in (".png", ".svg", ".jpg", ".jpeg", ".webp"):
            if file_nonempty(os.path.join(vdir, name)):
                stammen.add(stam.lower())
    return len(stammen)


def has_local_visuals(post_dir: str) -> bool:
    """True indien minimaal 1 beeldbestand in visuals/ aanwezig is."""
    return count_local_visuals(post_dir) > 0


def has_image_refs(post_dir: str) -> bool:
    """Beeldverwijzingen in draft.md tellen ook als visual."""
    draft = os.path.join(post_dir, ARTEFACT_FILES["draft"])
    if not file_nonempty(draft):
        return False
    with open(draft, encoding="utf-8") as f:
        return bool(IMAGE_REF_RE.search(f.read()))


def count_image_refs(post_dir: str) -> int:
    """Tel unieke beeldverwijzingen in draft.md."""
    draft = os.path.join(post_dir, ARTEFACT_FILES["draft"])
    if not file_nonempty(draft):
        return 0
    with open(draft, encoding="utf-8") as f:
        return len({m.group(1).strip() for m in IMAGE_REF_RE.finditer(f.read())})


def count_visuals(post_dir: str) -> int:
    """Aantal visuals bij deze post: het hoogste van bestanden en verwijzingen."""
    return max(count_local_visuals(post_dir), count_image_refs(post_dir))


def has_visuals(post_dir: str) -> bool:
    """Controleert of voldaan is aan de huisstijl-eis van minimaal 2 visuals."""
    return count_visuals(post_dir) >= MIN_VISUALS


def probe_artefacts(post_dir: str) -> dict[str, str]:
    """Inspecteer de schijf op de aanwezigheid van verwachte tussenartefacten."""
    out: dict[str, str] = {}
    for key, fname in ARTEFACT_FILES.items():
        out[key] = "present" if file_nonempty(os.path.join(post_dir, fname)) else "missing"
    out["visuals"] = "present" if has_visuals(post_dir) else "missing"
    return out
