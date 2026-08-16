"""Pure Python API Service Layer voor de blogpost workflow.

Deze klasse bundelt alle functionaliteit van de orkestrator zonder strakke koppeling
met CLI argumenten of sys.stdout. Zowel de CLI wrapper (orchestrate.py) als de Web UI
(FastAPI server) maken gebruik van deze service.
"""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from typing import Any

from .briefs import agent_brief
from .constants import (
    BLOCK_FOR_PHASE,
    BLOCK_LABELS,
    CONDITIONAL_GATES,
    FLAG_NAMES,
    PHASE_LABELS,
    PHASES,
    PHASES_DERIVED_FROM_DRAFT,
)
from .engine import (
    _precheck_run_clean,
    apply_approve_advance,
    compute_next,
    maybe_auto_approve,
    postcheck_complete,
)
from .formatters import (
    build_block_summary,
    build_phase_table,
    parse_state_md,
    render_phase_table_md,
)
from .probes import probe_artefacts
from .repository import (
    append_log,
    draft_fingerprint,
    empty_state,
    load_state,
    record_derivation,
    stale_phases,
    unrecorded_phases,
    now_iso,
    posts_root,
    resolve_post_dir,
    save_state,
    state_path,
    sync_artefact_flags,
    today,
)


from .archival_validator import (
    apply_alignment_verdict,
    ingest_alignment_report,
    read_alignment_verdict,
    resolve_alignment_discrepancy,
)
from .rag_archive import archive_vectorstore
from . import revision
from . import worker_status
from .synthesis import read_points, record_decision
from .synthesis import summarize as synthesis_summary
from .verdicts import (
    collect_findings,
    read_phase_findings,
    render_findings_md,
    summarize,
)


def _record_deploy_approval(state: dict[str, Any], post_dir: str) -> None:
    """Leg vast wélke draft is goedgekeurd voor deploy.

    Zonder deze koppeling overleeft `deploy_approved` een correctieronde en geeft de
    deploy-gate groen licht op een tekst die inmiddels is herschreven.
    """
    state["deploy_approval"] = {
        "draft_sha": draft_fingerprint(post_dir),
        "at": now_iso(),
    }


class WorkflowService:
    """Service API voor beheer van blogpost workflows."""

    def posts_root(self) -> str:
        """Geef het absolute pad naar de posts root map terug."""
        return posts_root()

    def get_worker_status(self) -> dict[str, Any]:
        """Lees of de execution-plane worker leeft, en zo ja welke job hij draait."""
        return worker_status.read_status()

    def resolve_dir(self, post: str | None = None, post_dir: str | None = None) -> str:
        return resolve_post_dir(post, post_dir)

    def init_post(
        self,
        slug: str,
        titel: str,
        yolo: bool = False,
        force: bool = False,
        wait_intake_gate: bool = False,
        post_dir: str | None = None,
    ) -> dict[str, Any]:
        """Initialiseer een nieuwe postmap met state.json."""
        clean_slug = slug.strip()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", clean_slug):
            raise ValueError("Slug moet kebab-case zijn: [a-z0-9]+(-[a-z0-9]+)*")
        if post_dir:
            pdir = os.path.abspath(post_dir)
        else:
            pdir = os.path.join(posts_root(), clean_slug)
        os.makedirs(pdir, exist_ok=True)
        path = state_path(pdir)
        if os.path.isfile(path) and not force:
            raise FileExistsError(f"state.json bestaat al: {path}")
        state = empty_state(clean_slug, titel, yolo=yolo)
        if wait_intake_gate:
            state["phase"] = "intake"
            state["status"] = "waiting_gate"
            state["gate"]["pending"] = "intake"
        save_state(pdir, state)
        return {"ok": True, "post_dir": pdir, "state": state}

    def get_status(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Haal uitgebreide status en vervolgactie op van een post."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        sync_artefact_flags(state, pdir)
        action = compute_next(state, pdir)
        return {
            "post_dir": pdir,
            "slug": state["slug"],
            "titel": state["titel"],
            "phase": state["phase"],
            "phase_label": PHASE_LABELS.get(state["phase"], state["phase"]),
            "block": BLOCK_FOR_PHASE.get(state["phase"], "bouwen"),
            "block_label": BLOCK_LABELS.get(BLOCK_FOR_PHASE.get(state["phase"], "bouwen")),
            "status": state["status"],
            "yolo_mode": state["yolo_mode"],
            "flags": state["flags"],
            "gate": state["gate"],
            "blocked_reason": state.get("blocked_reason"),
            "artefacts": state["artefacts"],
            "archival_alignment": state.get("archival_alignment"),
            "verdicts": state.get("verdicts") or {},
            "next": action,
        }

    def get_findings(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Bundel de bevindingen van alle controlefases (ADR-010 §6, stap 3).

        Afgeleid uit de rapporten op schijf, niet uit een opgeslagen kopie: die zou
        verouderen zodra een controle opnieuw draait.
        """
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        bundel = collect_findings(pdir, state)
        return {
            "slug": state["slug"],
            **bundel,
            "markdown": render_findings_md(bundel),
        }

    def get_synthesis(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Toon de kritiekpunten met hun varianten en de genomen beslissingen."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        return {"slug": state["slug"], **synthesis_summary(state, read_points(pdir))}

    def decide_point(
        self,
        punt_id: str,
        keuze: str,
        motivering: str,
        post: str | None = None,
        post_dir: str | None = None,
    ) -> dict[str, Any]:
        """Leg de beslissing van de auteur bij één kritiekpunt vast (ADR-010 §3.3).

        Per punt, met een motivering. Akkoord op het geheel is geen beslissing: zo bleef
        bij deel 2 een sectie staan die eruit had gemoeten.
        """
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        punten = read_points(pdir)

        punt = next((p for p in punten if p["id"] == punt_id), None)
        if punt is None:
            bekend = ", ".join(p["id"] for p in punten) or "geen"
            raise ValueError(f"Onbekend punt '{punt_id}'. Bekende punten: {bekend}.")

        record_decision(state, punt, keuze, motivering, now_iso())
        append_log(
            state,
            "synthese_besluit",
            note=f"{punt_id}: {keuze} — {motivering.strip()}",
            phase="synthesis",
        )
        save_state(pdir, state)
        return {"ok": True, "punt": punt_id, "keuze": keuze, **synthesis_summary(state, punten)}

    def get_revisions(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Toon de opmerkingen van de auteur na het lezen (ADR-010 §3.4)."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        return {"slug": state["slug"], **revision.summarize(pdir)}

    def add_revision(
        self,
        opmerking: str,
        waar: str = "",
        post: str | None = None,
        post_dir: str | None = None,
    ) -> dict[str, Any]:
        """Leg een opmerking van de auteur vast als artefact.

        Bij deel 2 kwamen de drie inhoudelijke opmerkingen na het lezen in WordPress en
        stonden ze nergens; ze bestonden alleen in een gesprek.
        """
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        punt = revision.add(pdir, opmerking, waar, state["titel"], now_iso())
        append_log(state, "revisiepunt_toegevoegd", note=f"{punt['id']}: {punt['opmerking']}")
        save_state(pdir, state)
        return {"ok": True, "punt": punt, **revision.summarize(pdir)}

    def close_revision(
        self,
        punt_id: str,
        hoe: str,
        post: str | None = None,
        post_dir: str | None = None,
    ) -> dict[str, Any]:
        """Markeer een opmerking als verwerkt, met hoe."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        punt = revision.close(pdir, punt_id, hoe, state["titel"])
        append_log(state, "revisiepunt_afgehandeld", note=f"{punt['id']}: {punt['afgehandeld']}")
        save_state(pdir, state)
        return {"ok": True, "punt": punt, **revision.summarize(pdir)}

    def start_revision_round(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Open een herzieningsronde: terug naar de draft met de opmerkingen als opdracht.

        Dit is de lus uit ADR-010 §3.1: na het lezen in WordPress gaat de post terug het
        Bouwen-blok in. De vingerafdrukken uit stap 1 markeren daarna vanzelf welke
        controles opnieuw moeten.
        """
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        openstaand = revision.open_points(revision.read_points(pdir))
        if not openstaand:
            raise ValueError(
                "Geen openstaande revisiepunten. Voeg eerst je opmerkingen toe met "
                "`revisie --opmerking \"...\"`."
            )

        state["phase"] = "draft"
        state["status"] = "ready"
        state["gate"]["pending"] = None
        state["blocked_reason"] = None
        append_log(
            state,
            "herzieningsronde_gestart",
            note=f"{len(openstaand)} punt(en): {', '.join(p['id'] for p in openstaand)}",
            phase="draft",
        )
        save_state(pdir, state)
        return {"ok": True, "phase": state["phase"], "open": len(openstaand), "punten": openstaand}

    def get_table(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Bereken de statustabel per fase."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        sync_artefact_flags(state, pdir)
        rows = build_phase_table(state, pdir)
        md = render_phase_table_md(state, rows)
        return {
            "slug": state["slug"],
            "titel": state["titel"],
            "rows": rows,
            "blocks": build_block_summary(state, rows),
            "markdown": md,
        }

    def get_next(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Haal de eerstvolgende toegestane actie op."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        sync_artefact_flags(state, pdir)
        return compute_next(state, pdir)

    def run_phase(
        self, phase: str, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Start de uitvoering van een runnable fase."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        errors = _precheck_run_clean(phase, state, pdir)
        if errors:
            return {"ok": False, "errors": errors}

        if phase == "visuals" and state["phase"] != "visuals" and state["flags"].get("defer_critique"):
            append_log(
                state,
                "defer_critique_visuals_run",
                note=f"visuals gestart terwijl phase={state['phase']}",
                phase=state["phase"],
            )
            state["phase"] = "visuals"

        state["status"] = "running"
        state["blocked_reason"] = None
        state["gate"]["pending"] = None
        append_log(state, "run_started", phase=phase)
        sync_artefact_flags(state, pdir)
        save_state(pdir, state)

        brief = agent_brief(phase, pdir, state)
        return {
            "ok": True,
            "phase": phase,
            "status": "running",
            "agent_brief": brief,
            "note": f"Voer de agent/script uit; daarna: complete {phase}",
        }

    def complete_phase(
        self,
        phase: str,
        post: str | None = None,
        post_dir: str | None = None,
        post_id: int | None = None,
        edit_url: str | None = None,
    ) -> dict[str, Any]:
        """Rond de uitvoering van een fase af."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)

        if state["phase"] != phase and not (
            phase == "visuals" and state["flags"].get("defer_critique")
        ):
            return {
                "ok": False,
                "errors": [f"Phase is '{state['phase']}', complete '{phase}' geweigerd."],
            }

        if state["status"] == "waiting_gate" and state["phase"] == phase:
            return {"ok": False, "errors": ["Al waiting_gate; gebruik approve/reject."]}

        errors = postcheck_complete(phase, state, pdir, post_id=post_id, edit_url=edit_url)
        if errors:
            state["status"] = "blocked"
            state["blocked_reason"] = "; ".join(errors)
            append_log(state, "complete_failed", note=state["blocked_reason"], phase=phase)
            save_state(pdir, state)
            return {"ok": False, "errors": errors, "status": "blocked"}

        if phase == "deploy":
            if post_id:
                state["artefacts"]["wp_post_id"] = post_id
            if edit_url:
                state["artefacts"]["edit_url"] = edit_url

        sync_artefact_flags(state, pdir)
        state["phase"] = phase
        state["blocked_reason"] = None
        append_log(state, "complete_ok", phase=phase)

        if phase in PHASES_DERIVED_FROM_DRAFT:
            # Leg vast van welke draft dit rapport is afgeleid, zodat een latere
            # tekstwijziging zichtbaar maakt dat het verouderd is (ADR-010 §3.5).
            record_derivation(state, phase, pdir)

        if phase in CONDITIONAL_GATES:
            # De postcheck heeft het bevindingenblok al gevalideerd; hier landt de telling
            # in state.json, zodat de gate weet of er iets voor te leggen is (ADR-010 §3.1).
            samenvatting = summarize(read_phase_findings(pdir, phase))
            state.setdefault("verdicts", {})[phase] = samenvatting
            append_log(
                state,
                "verdict_recorded",
                note=f"{samenvatting['blocking']} blokkerend, {samenvatting['advisory']} ter overweging",
                phase=phase,
            )

        if phase == "alignment":
            # De postcheck heeft het rapport al gevalideerd; hier landt het verdict in
            # state.json, zodat de gate-logica weet of er een bevinding is (ADR-007).
            verdict = read_alignment_verdict(pdir)
            discrepant = apply_alignment_verdict(state, verdict)
            append_log(
                state,
                "alignment_discrepancy_found" if discrepant else "alignment_ok",
                note=f"{len(verdict['discrepancies'])} bevinding(en)" if discrepant else None,
                phase="alignment",
            )

        yolo_advanced = maybe_auto_approve(state, phase)
        if not yolo_advanced:
            state["status"] = "waiting_gate"
            state["gate"]["pending"] = phase

        save_state(pdir, state)
        return {
            "ok": True,
            "phase": state["phase"],
            "status": state["status"],
            "yolo_advanced": yolo_advanced,
            "gate": state["gate"],
            "next": compute_next(state, pdir),
        }

    def approve_gate(
        self,
        post: str | None = None,
        post_dir: str | None = None,
        note: str | None = None,
        deploy: bool = False,
    ) -> dict[str, Any]:
        """Keur een gate akkoord en schuif door naar de volgende fase."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)

        if deploy:
            state["flags"]["deploy_approved"] = True
            _record_deploy_approval(state, pdir)
            append_log(state, "deploy_approved_set", note=note)
            if state["phase"] == "deploy" and state["status"] == "ready":
                save_state(pdir, state)
                return {
                    "ok": True,
                    "flags": state["flags"],
                    "next": compute_next(state, pdir),
                }

        if state["status"] != "waiting_gate" and state["phase"] != "intake":
            if not (state["phase"] == "intake" and state["status"] in {"ready", "waiting_gate"}):
                if deploy and state["status"] != "waiting_gate":
                    save_state(pdir, state)
                    return {
                        "ok": True,
                        "note": "deploy_approved gezet; pipeline-gate niet van toepassing",
                        "flags": state["flags"],
                        "next": compute_next(state, pdir),
                    }
                return {
                    "ok": False,
                    "errors": [f"Approve alleen bij waiting_gate (nu: {state['status']})."],
                }

        if state["phase"] == "deploy" and state["status"] == "waiting_gate":
            if not state["flags"].get("deploy_approved") and not deploy:
                state["flags"]["deploy_approved"] = True
            apply_approve_advance(state, note, deploy=True)
        else:
            apply_approve_advance(state, note, deploy=deploy)

        if state["phase"] == "synthesis" and state["flags"].get("skip_synthesis"):
            state["phase"] = "visuals"
            append_log(state, "skip_synthesis_applied", note="phase → visuals")

        sync_artefact_flags(state, pdir)
        save_state(pdir, state)
        return {
            "ok": True,
            "phase": state["phase"],
            "status": state["status"],
            "next": compute_next(state, pdir),
        }

    def reject_gate(
        self,
        post: str | None = None,
        post_dir: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Wijs een gate af en zet de status terug op ready."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        if state["status"] not in {"waiting_gate", "blocked", "running"}:
            return {
                "ok": False,
                "errors": [f"Reject niet zinvol bij status {state['status']}."],
            }
        phase = state["gate"].get("pending") or state["phase"]
        state["gate"]["last_decision"] = {
            "at": now_iso(),
            "decision": "reject",
            "phase": phase,
            "note": note,
        }
        state["gate"]["pending"] = None
        state["status"] = "ready"
        state["phase"] = phase if phase in PHASES else state["phase"]
        state["blocked_reason"] = None
        append_log(state, "gate_rejected", note=note, phase=phase)
        save_state(pdir, state)
        return {
            "ok": True,
            "phase": state["phase"],
            "status": "ready",
            "next": compute_next(state, pdir),
        }

    def mark_blocked(
        self,
        reason: str,
        post: str | None = None,
        post_dir: str | None = None,
    ) -> dict[str, Any]:
        """Zet de huidige fase op blocked. Alleen voor uitvoeringsfouten.

        De worker roept dit aan als `claude -p` faalt of een timeout raakt,
        zodat de post niet stilletjes op `running` blijft staan. Dit is geen
        gate-beslissing: approve blijft bij de auteur (ADR-010).
        """
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        text = (reason or "").strip() or "uitvoering gefaald, geen reden gegeven"
        state["status"] = "blocked"
        state["blocked_reason"] = text
        append_log(state, "execution_failed", note=text, phase=state["phase"])
        save_state(pdir, state)
        return {
            "ok": True,
            "phase": state["phase"],
            "status": "blocked",
            "blocked_reason": text,
        }

    def set_flag(
        self,
        name: str,
        value: bool,
        post: str | None = None,
        post_dir: str | None = None,
    ) -> dict[str, Any]:
        """Zet yolo_mode of een specifieke vlag (skip_synthesis, etc.)."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        if name == "yolo_mode":
            state["yolo_mode"] = value
            append_log(state, "flag_set", note=f"yolo_mode={value}")
        elif name in FLAG_NAMES:
            state["flags"][name] = value
            if name == "deploy_approved":
                if value:
                    _record_deploy_approval(state, pdir)
                else:
                    state["deploy_approval"] = None
            append_log(state, "flag_set", note=f"{name}={value}")
        else:
            raise ValueError(f"Onbekende flag: {name}. Kies: yolo_mode, {', '.join(FLAG_NAMES)}")
        save_state(pdir, state)
        return {
            "ok": True,
            "yolo_mode": state["yolo_mode"],
            "flags": state["flags"],
        }

    def doctor(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Inspecteer de integriteit en eventuele drift van state vs. schijf met schone helper functies."""
        pdir = self.resolve_dir(post, post_dir)
        if not os.path.isdir(pdir):
            return {"ok": False, "errors": [f"Map ontbreekt: {pdir}"]}

        if not os.path.isfile(state_path(pdir)):
            issues = [{"severity": "error", "msg": "state.json ontbreekt — run import-md of init"}]
            return {"ok": False, "issues": issues, "probed": probe_artefacts(pdir)}

        state = load_state(pdir)
        probed = probe_artefacts(pdir)

        issues: list[dict[str, str]] = []
        issues.extend(_check_state_vs_disk_drift(state, probed))
        issues.extend(_check_linear_artefact_consistency(state, probed))

        phase_issues, hard_errors = _check_phase_artefact_prerequisites(state, probed)
        issues.extend(phase_issues)
        issues.extend(_check_status_and_flag_consistency(state, probed))
        issues.extend(_check_report_freshness(state, pdir, probed))

        return {
            "ok": hard_errors == 0,
            "slug": state["slug"],
            "phase": state["phase"],
            "status": state["status"],
            "flags": state["flags"],
            "probed": probed,
            "stored_artefacts": state["artefacts"],
            "issues": issues,
            "next": compute_next(state, pdir),
        }

    def import_md(
        self,
        post: str | None = None,
        post_dir: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Importeer een legacy state.md bestand naar state.json."""
        pdir = self.resolve_dir(post, post_dir)
        md_path = os.path.join(pdir, "state.md")
        if not os.path.isfile(md_path):
            raise FileNotFoundError(f"Geen state.md in {pdir}")
        if os.path.isfile(state_path(pdir)) and not force:
            raise FileExistsError("state.json bestaat al; gebruik force=True om te overschrijven")

        parsed = parse_state_md(md_path)
        meta = parsed["meta"]
        slug = meta.get("slug") or os.path.basename(pdir.rstrip("/"))
        titel = meta.get("titel") or slug
        aangemaakt = meta.get("aangemaakt") or today()

        state = empty_state(slug, titel, yolo=parsed["yolo_mode"])
        state["aangemaakt"] = aangemaakt
        state["phase"] = parsed["phase"]
        state["status"] = parsed["status"]
        state["flags"]["skip_synthesis"] = parsed["skip_synthesis"]
        state["flags"]["defer_critique"] = parsed["defer_critique"]
        if parsed["wp_post_id"]:
            state["artefacts"]["wp_post_id"] = parsed["wp_post_id"]
            state["flags"]["deploy_approved"] = True
        if parsed["edit_url"]:
            state["artefacts"]["edit_url"] = parsed["edit_url"]

        sync_artefact_flags(state, pdir)
        if state["phase"] == "done":
            state["status"] = "done"

        note = (
            f"import-md uit state.md; huidige_fase_raw={parsed.get('huidige_fase_raw')!r}; "
            f"flags skip_synthesis={state['flags']['skip_synthesis']} "
            f"defer_critique={state['flags']['defer_critique']}"
        )
        append_log(state, "imported_from_md", note=note)
        save_state(pdir, state)
        return {"ok": True, "state": state, "doctor_hint": "run doctor"}

    def render_md(
        self,
        post: str | None = None,
        post_dir: str | None = None,
        in_place: bool = False,
    ) -> dict[str, Any]:
        """Projecteer state.json naar een leesbaar Markdown-bestand."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        sync_artefact_flags(state, pdir)
        out_path = os.path.join(pdir, "state.generated.md")
        if in_place:
            out_path = os.path.join(pdir, "state.md")

        lines = [
            "---",
            f"slug: {state['slug']}",
            f"titel: {state['titel']}",
            f"aangemaakt: {state['aangemaakt']}",
            f"phase: {state['phase']}",
            f"status: {state['status']}",
            f"yolo_mode: {'aan' if state['yolo_mode'] else 'uit'}",
            "---",
            "",
            f"# Staat — {state['titel']}",
            "",
            "Gegenereerd door `scripts/orchestrate.py render-md`. Bron van waarheid: `state.json`.",
            "",
            "## Status",
            "",
            f"- **Phase:** {state['phase']} ({PHASE_LABELS.get(state['phase'], '')})",
            f"- **Status:** {state['status']}",
            f"- **Flags:** `{json.dumps(state['flags'], ensure_ascii=False)}`",
            f"- **Gate:** `{json.dumps(state['gate'], ensure_ascii=False)}`",
            "",
            "## Artefacts",
            "",
            f"```json\n{json.dumps(state['artefacts'], ensure_ascii=False, indent=2)}\n```",
            "",
            "## Log (recent)",
            "",
        ]
        for entry in state.get("log", [])[-20:]:
            lines.append(
                f"- {entry.get('at')} — {entry.get('event')}"
                + (f" — {entry.get('phase')}" if entry.get("phase") else "")
                + (f" — {entry.get('note')}" if entry.get("note") else "")
            )
        lines.append("")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return {"ok": True, "path": out_path}

    def repair(
        self,
        post: str | None = None,
        post_dir: str | None = None,
        apply: bool = False,
    ) -> dict[str, Any]:
        """Herleid phase/status uit artefacten op schijf."""
        pdir = self.resolve_dir(post, post_dir)
        state = load_state(pdir)
        probed = probe_artefacts(pdir)
        proposal = deepcopy(state)

        if probed["outline"] != "present":
            proposal["phase"] = "outline"
            proposal["status"] = "ready"
        elif probed["draft"] != "present":
            proposal["phase"] = "draft"
            proposal["status"] = "ready"
        else:
            if probed["grok_feedback"] != "present":
                if state["flags"].get("defer_critique") and probed["visuals"] == "present":
                    proposal["phase"] = "critique"
                    proposal["status"] = "ready"
                else:
                    if state["phase"] in {"style", "series", "draft"}:
                        proposal["phase"] = state["phase"] if state["phase"] != "draft" else "style"
                        proposal["status"] = "ready"
                    else:
                        proposal["phase"] = "style"
                        proposal["status"] = "ready"
            elif probed["synthese"] != "present" and not state["flags"].get("skip_synthesis"):
                proposal["phase"] = "synthesis"
                proposal["status"] = "ready"
            elif probed["visuals"] != "present":
                proposal["phase"] = "visuals"
                proposal["status"] = "ready"
            elif state["artefacts"].get("wp_post_id") or proposal["artefacts"].get("wp_post_id"):
                proposal["phase"] = "done"
                proposal["status"] = "done"
            else:
                proposal["phase"] = "deploy"
                proposal["status"] = "ready"

        wp = state["artefacts"].get("wp_post_id")
        if wp:
            proposal["artefacts"]["wp_post_id"] = wp
            proposal["phase"] = "done"
            proposal["status"] = "done"
            proposal["flags"]["deploy_approved"] = True

        sync_artefact_flags(proposal, pdir)

        out = {
            "current": {"phase": state["phase"], "status": state["status"]},
            "proposal": {
                "phase": proposal["phase"],
                "status": proposal["status"],
                "flags": proposal["flags"],
            },
            "probed": probed,
            "applied": False,
        }
        if apply:
            state["phase"] = proposal["phase"]
            state["status"] = proposal["status"]
            state["flags"] = proposal["flags"]
            sync_artefact_flags(state, pdir)
            append_log(state, "repair_applied", note=json.dumps(out["proposal"], ensure_ascii=False))
            save_state(pdir, state)
            out["applied"] = True
        return out

    def search_archive(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Zoek lexicaal (TF-IDF) in het live archief (ADR-006 §6).

        Herindexeert niet. De index is de laatste fetch van edwinvandillen.nl;
        vernieuwen loopt via reindex_archive / de Settings-tab.
        """
        return archive_vectorstore.search(query=query, top_k=top_k)

    def get_rag_status(self) -> dict[str, Any]:
        """Haal RAG index status en statistieken op (ADR-008)."""
        return archive_vectorstore.get_status()

    def reindex_archive(self, purge: bool = False, incremental: bool = False) -> dict[str, Any]:
        """Haal het live archief opnieuw op van edwinvandillen.nl (ADR-006 §6)."""
        count = archive_vectorstore.index_all_posts(
            posts_root(), incremental=incremental, purge=purge, include_wordpress=True
        )
        return {"ok": True, "indexed_chunks": count}

    def validate_alignment(
        self, post: str | None = None, post_dir: str | None = None
    ) -> dict[str, Any]:
        """Lees het verdict uit archief-consistentie.md in state.json (ADR-007).

        De inhoudelijke vergelijking doet de subagent archief-consistentie-check in fase
        5c; deze methode voert die check niet uit, ze leest alleen het resultaat. Ze
        verschuift de fase niet: dat loopt via `complete alignment`.
        """
        return ingest_alignment_report(post=post, post_dir=post_dir)

    def resolve_alignment(
        self,
        post: str | None = None,
        post_dir: str | None = None,
        action: str = "progressive_insight",
        note: str | None = None,
    ) -> dict[str, Any]:
        """Verwerk auteur beslissing bij inhoudelijke afwijking (ADR-007)."""
        return resolve_alignment_discrepancy(post=post, post_dir=post_dir, action=action, note=note)


def _check_report_freshness(
    state: dict[str, Any], post_dir: str, probed: dict[str, str]
) -> list[dict[str, str]]:
    """Meld rapporten die bij een oudere versie van draft.md horen (ADR-010 §3.5)."""
    aanwezig = [p for p in PHASES_DERIVED_FROM_DRAFT if probed.get(_ARTEFACT_VOOR_FASE.get(p, p)) == "present"]
    issues = [
        {
            "severity": "warning",
            "msg": f"rapport van fase '{p}' hoort bij een oudere draft; opnieuw draaien",
        }
        for p in stale_phases(state, post_dir, aanwezig)
    ]
    issues.extend(
        {
            "severity": "info",
            "msg": f"rapport van fase '{p}' heeft geen vingerafdruk; actualiteit niet te toetsen",
        }
        for p in unrecorded_phases(state, aanwezig)
    )
    return issues


#: Welke artefact-sleutel bepaalt of het rapport van een fase op schijf staat.
_ARTEFACT_VOOR_FASE = {
    "style": "stijlcheck",
    "series": "reeks_check",
    "factcheck": "factcheck",
    "alignment": "alignment",
}


def _check_state_vs_disk_drift(state: dict[str, Any], probed: dict[str, str]) -> list[dict[str, str]]:
    """Detecteer afwijkingen tussen opgeslagen artefact status in state.json en schijf."""
    issues = []
    for key, disk in probed.items():
        stored = state["artefacts"].get(key)
        if stored != disk:
            issues.append({"severity": "warning", "msg": f"artefacts.{key}: state={stored}, disk={disk}"})
    return issues


def _check_linear_artefact_consistency(state: dict[str, Any], probed: dict[str, str]) -> list[dict[str, str]]:
    """Controleer of latere artefacten aanwezig zijn terwijl eerdere nog ontbreken."""
    issues = []
    order = ["outline", "draft", "grok_feedback", "synthese", "visuals"]
    missing_before: set[str] = set()

    for key in order:
        if probed[key] == "missing":
            if key == "synthese" and state["flags"].get("skip_synthesis"):
                continue
            if key == "grok_feedback" and state["flags"].get("defer_critique") and probed.get("visuals") == "present":
                missing_before.add(key)
                continue
            missing_before.add(key)
            continue

        relevant_missing = set(missing_before)
        if key == "visuals" and state["flags"].get("skip_synthesis"):
            relevant_missing.discard("synthese")
        if key == "visuals" and state["flags"].get("defer_critique"):
            if relevant_missing <= {"grok_feedback", "synthese"}:
                continue

        if relevant_missing:
            issues.append(
                {
                    "severity": "warning",
                    "msg": (
                        f"{key} present terwijl eerdere artefacten missing: "
                        f"{sorted(relevant_missing)} (niet-lineair of ontbrekende flag)"
                    ),
                }
            )

    return issues


def _check_phase_artefact_prerequisites(state: dict[str, Any], probed: dict[str, str]) -> tuple[list[dict[str, str]], int]:
    """Controleer verplichte artefacten voor de huidige fase."""
    issues = []
    hard_errors = 0
    phase = state["phase"]
    advanced_phases = {"draft", "style", "series", "critique", "synthesis", "visuals", "deploy", "done"}

    if phase in advanced_phases and probed["outline"] != "present":
        issues.append({"severity": "error", "msg": f"phase={phase} maar outline.md mist"})
        hard_errors += 1

    post_draft_phases = {"style", "series", "critique", "synthesis", "visuals", "deploy", "done"}
    if phase in post_draft_phases and probed["draft"] != "present":
        issues.append({"severity": "error", "msg": f"phase={phase} maar draft.md mist"})
        hard_errors += 1

    return issues, hard_errors


def _check_status_and_flag_consistency(state: dict[str, Any], probed: dict[str, str]) -> list[dict[str, str]]:
    """Controleer vlaggen en status consistentie."""
    issues = []
    phase = state["phase"]

    if state["artefacts"].get("wp_post_id") and phase not in {"deploy", "done"}:
        issues.append({"severity": "warning", "msg": f"wp_post_id gezet maar phase={phase} (verwacht deploy/done of named exception)"})

    if phase == "done" and not state["artefacts"].get("wp_post_id"):
        issues.append({"severity": "warning", "msg": "phase=done zonder wp_post_id"})

    if state["flags"].get("skip_synthesis") and probed["synthese"] == "present":
        issues.append({"severity": "info", "msg": "skip_synthesis aan maar synthese.md bestaat wel"})

    if state["status"] == "waiting_gate" and not state["gate"].get("pending"):
        issues.append({"severity": "warning", "msg": "waiting_gate zonder gate.pending"})

    if state["status"] == "running":
        issues.append({"severity": "info", "msg": "status=running — complete of reject verwacht"})

    return issues
