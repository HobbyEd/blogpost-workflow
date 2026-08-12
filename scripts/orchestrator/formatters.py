"""Statustabel formatters en legacy state.md parser voor de blogpost workflow."""

from __future__ import annotations

import re
from typing import Any

from .constants import (
    ARTEFACT_FILES,
    PHASE_ARTEFACT_KEY,
    PHASE_LABELS,
    PHASES,
)
from .probes import probe_artefacts


def _artefact_cell(phase: str, state: dict[str, Any], probed: dict[str, Any]) -> str:
    key = PHASE_ARTEFACT_KEY.get(phase)
    if key is None:
        return "—"
    if key == "visuals":
        return "visuals/*" if probed.get("visuals") == "present" else "visuals/ (leeg)"
    if key == "deploy":
        wp = state["artefacts"].get("wp_post_id")
        return f"post {wp}" if wp else "—"
    fname = ARTEFACT_FILES.get(key, key)
    return fname if probed.get(key) == "present" else f"{fname} (ontbreekt)"


def build_phase_table(state: dict[str, Any], post_dir: str) -> list[dict[str, str]]:
    """Bereken de statustabel puur uit state.json + bestanden op schijf."""
    probed = probe_artefacts(post_dir)
    flags = state["flags"]
    cur_idx = PHASES.index(state["phase"])
    gate_note = state["gate"].get("last_decision") or {}

    rows: list[dict[str, str]] = []
    for phase in PHASES:
        idx = PHASES.index(phase)
        label = PHASE_LABELS.get(phase, phase)
        status_label, note = _determine_phase_row_status(phase, idx, cur_idx, state, flags, gate_note)

        rows.append(
            {
                "phase": phase,
                "label": label,
                "status": status_label,
                "artefact": _artefact_cell(phase, state, probed),
                "note": note,
            }
        )
    return rows


def _determine_phase_row_status(
    phase: str,
    idx: int,
    cur_idx: int,
    state: dict[str, Any],
    flags: dict[str, Any],
    gate_note: dict[str, Any],
) -> tuple[str, str]:
    """Herleid de status_label en opmerking voor een specifieke fase in de tabel."""
    if phase == "synthesis" and flags.get("skip_synthesis"):
        return "overgeslagen", "skip_synthesis"

    if phase == "critique" and flags.get("defer_critique") and idx < cur_idx:
        return "uitgesteld", "defer_critique"

    if idx < cur_idx:
        note = gate_note["note"] if gate_note.get("phase") == phase and gate_note.get("note") else ""
        return "gereed", note

    if idx == cur_idx:
        return _determine_current_phase_status(state)

    return "open", ""


def _determine_current_phase_status(state: dict[str, Any]) -> tuple[str, str]:
    """Herleid de status van de momenteel actieve fase."""
    st = state["status"]
    if st == "running":
        return "bezig", ""
    if st == "waiting_gate":
        return "wacht op gate", ""
    if st == "blocked":
        return "geblokkeerd", state.get("blocked_reason") or ""
    if st == "done":
        return "gereed", ""

    phase = state["phase"]
    status_text = "open" if phase == "done" else "klaar om te starten"
    return status_text, ""


def render_phase_table_md(state: dict[str, Any], rows: list[dict[str, str]]) -> str:
    """Render de statustabel als Markdown string."""
    lines = [
        f"**{state['titel']}** (`{state['slug']}`) — yolo: {'aan' if state['yolo_mode'] else 'uit'}",
        "",
        "| Fase | Status | Artefact | Opmerking |",
        "|---|---|---|---|",
    ]
    for r in rows:
        if r["phase"] == "done":
            continue
        lines.append(f"| {r['label']} | {r['status']} | {r['artefact']} | {r['note']} |")
    if state["phase"] == "done":
        lines.append("")
        lines.append("Pipeline: **klaar** (concept staat op WordPress).")
    return "\n".join(lines) + "\n"


def parse_state_md(path: str) -> dict[str, Any]:
    """Best-effort parse van legacy state.md frontmatter + tabel + beslislog-hints."""
    text = open(path, encoding="utf-8").read()
    meta = _parse_md_frontmatter(text)

    row_re = re.compile(
        r"^\|\s*(\d+[a-z]?)\s*\|\s*([^|]+?)\s*\|\s*(gereed|open|bezig|afgekeurd)\s*\|",
        re.I | re.M,
    )
    rows: list[tuple[str, str, str]] = [
        (rm.group(1).lower(), rm.group(2).strip().lower(), rm.group(3).lower())
        for rm in row_re.finditer(text)
    ]

    def row_status(num: str) -> str | None:
        for n, _name, st in rows:
            if n == num:
                return st
        return None

    skill_to_phase = {
        "0": "intake",
        "1": "outline",
        "2": "draft",
        "2b": "style",
        "2c": "series",
        "3": "critique",
        "4": "synthesis",
        "5": "visuals",
        "6": "deploy",
    }

    order_nums = ["0", "1", "2", "2b", "2c", "3", "4", "5", "6"]
    present_nums = [n for n in order_nums if row_status(n) is not None] or [n for n in order_nums if n != "2c"]

    current_phase, current_status = _infer_phase_from_legacy_rows(present_nums, row_status, skill_to_phase)

    critique_open = row_status("3") in {None, "open", "bezig"}
    visuals_gereed = row_status("5") == "gereed"
    deploy_gereed = row_status("6") == "gereed"
    synthesis_open = row_status("4") in {None, "open", "bezig"}

    defer_critique = (visuals_gereed or deploy_gereed) and critique_open
    skip_synthesis = deploy_gereed and synthesis_open

    if deploy_gereed:
        current_phase = "done"
        current_status = "done"

    yolo = meta.get("yolo_mode", "uit").lower() in {"aan", "true", "1", "yes"}
    wp_id, edit_url = _extract_wp_credentials_from_md(text)

    return {
        "meta": meta,
        "phase": current_phase,
        "status": current_status,
        "yolo_mode": yolo,
        "skip_synthesis": skip_synthesis,
        "defer_critique": defer_critique,
        "wp_post_id": wp_id,
        "edit_url": edit_url,
        "huidige_fase_raw": meta.get("huidige_fase", ""),
    }


def _parse_md_frontmatter(text: str) -> dict[str, str]:
    """Parse YAML frontmatter uit markdown string."""
    meta: dict[str, str] = {}
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return meta
    for line in match.group(1).splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
    return meta


def _infer_phase_from_legacy_rows(
    present_nums: list[str],
    row_status_fn: Any,
    skill_to_phase: dict[str, str],
) -> tuple[str, str]:
    """Herleid de huidige fase en status uit de rijen van state.md."""
    first_open = next((n for n in present_nums if row_status_fn(n) in {"open", "bezig", "afgekeurd"}), None)
    all_gereed = all(row_status_fn(n) == "gereed" for n in present_nums if row_status_fn(n))

    if all_gereed and present_nums:
        return ("done", "done") if row_status_fn("6") == "gereed" else ("outline", "ready")

    if first_open:
        phase = skill_to_phase.get(first_open, "outline")
        st = row_status_fn(first_open)
        status = "running" if st == "bezig" else "ready"
        return phase, status

    return "outline", "ready"


def _extract_wp_credentials_from_md(text: str) -> tuple[int | None, str | None]:
    """Extraheer WordPress post_id en edit_url uit markdown tekst."""
    wp_id = None
    edit_url = None

    id_m = re.search(r"post-id\s*(\d+)", text, re.I)
    if id_m:
        wp_id = int(id_m.group(1))

    url_m = re.search(r"https?://[^\s\"']+/wp-admin/post\.php\?post=\d+&action=edit", text)
    if url_m:
        edit_url = url_m.group(0)

    return wp_id, edit_url
