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
        note = ""
        status_label: str

        if phase == "synthesis" and flags.get("skip_synthesis"):
            status_label = "overgeslagen"
            note = "skip_synthesis"
        elif phase == "critique" and flags.get("defer_critique") and idx < cur_idx:
            status_label = "uitgesteld"
            note = "defer_critique"
        elif idx < cur_idx:
            status_label = "gereed"
            if gate_note.get("phase") == phase and gate_note.get("note"):
                note = gate_note["note"]
        elif idx == cur_idx:
            st = state["status"]
            if st == "running":
                status_label = "bezig"
            elif st == "waiting_gate":
                status_label = "wacht op gate"
            elif st == "blocked":
                status_label = "geblokkeerd"
                note = state.get("blocked_reason") or ""
            elif st == "done":
                status_label = "gereed"
            else:
                status_label = "open" if phase == "done" else "klaar om te starten"
        else:
            status_label = "open"

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
    meta: dict[str, str] = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()

    row_re = re.compile(
        r"^\|\s*(\d+[a-z]?)\s*\|\s*([^|]+?)\s*\|\s*(gereed|open|bezig|afgekeurd)\s*\|",
        re.I | re.M,
    )
    rows: list[tuple[str, str, str]] = []
    for rm in row_re.finditer(text):
        rows.append((rm.group(1).lower(), rm.group(2).strip().lower(), rm.group(3).lower()))

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
    present_nums = [n for n in order_nums if row_status(n) is not None]
    if not present_nums:
        present_nums = [n for n in order_nums if n != "2c"]

    current_phase = "outline"
    current_status = "ready"
    skip_synthesis = False
    defer_critique = False

    first_open = None
    for n in present_nums:
        st = row_status(n)
        if st in {"open", "bezig", "afgekeurd"}:
            first_open = n
            break

    all_gereed = all(row_status(n) == "gereed" for n in present_nums if row_status(n))

    if all_gereed and present_nums:
        if row_status("6") == "gereed":
            current_phase = "done"
            current_status = "done"
        else:
            current_phase = "outline"
            current_status = "ready"
    elif first_open:
        current_phase = skill_to_phase.get(first_open, "outline")
        st = row_status(first_open)
        if st == "bezig":
            current_status = "running"
        elif st == "afgekeurd":
            current_status = "ready"
        else:
            current_status = "ready"

    critique_open = row_status("3") in {None, "open", "bezig"}
    visuals_gereed = row_status("5") == "gereed"
    deploy_gereed = row_status("6") == "gereed"
    synthesis_open = row_status("4") in {None, "open", "bezig"}

    if (visuals_gereed or deploy_gereed) and critique_open:
        defer_critique = True
    if deploy_gereed and synthesis_open:
        skip_synthesis = True
    if deploy_gereed and row_status("6") == "gereed":
        current_phase = "done"
        current_status = "done"

    hf = meta.get("huidige_fase", "")
    if deploy_gereed:
        current_phase = "done"
        current_status = "done"

    yolo = meta.get("yolo_mode", "uit").lower() in {"aan", "true", "1", "yes"}

    wp_id = None
    edit_url = None
    id_m = re.search(r"post-id\s*(\d+)", text, re.I)
    if id_m:
        wp_id = int(id_m.group(1))
    url_m = re.search(r"https?://[^\s\"']+/wp-admin/post\.php\?post=\d+&action=edit", text)
    if url_m:
        edit_url = url_m.group(0)

    return {
        "meta": meta,
        "phase": current_phase,
        "status": current_status,
        "yolo_mode": yolo,
        "skip_synthesis": skip_synthesis,
        "defer_critique": defer_critique,
        "wp_post_id": wp_id,
        "edit_url": edit_url,
        "huidige_fase_raw": hf,
    }
