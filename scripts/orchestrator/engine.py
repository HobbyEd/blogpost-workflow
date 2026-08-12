"""State machine transitielogica en pre/postchecks voor de blogpost workflow."""

from __future__ import annotations

import os
from typing import Any

from .briefs import agent_brief
from .constants import (
    ARTEFACT_FILES,
    HARD_GATES,
    MIN_VISUALS,
    PHASES,
    RUNNABLE,
    SOFT_GATES,
)
from .probes import count_visuals, probe_artefacts
from .repository import append_log, now_iso


def next_phase_after(phase: str, flags: dict[str, Any]) -> str:
    """Bepaal de eerstvolgende logische fase in de pijplijn."""
    if phase == "critique" and flags.get("skip_synthesis"):
        return "visuals"
    if phase == "deploy":
        return "done"
    if phase == "done":
        return "done"
    try:
        i = PHASES.index(phase)
    except ValueError:
        raise ValueError(f"Onbekende phase: {phase}") from None
    if i + 1 >= len(PHASES):
        return "done"
    nxt = PHASES[i + 1]
    if nxt == "intake":
        nxt = "outline"
    return nxt


def gate_type(phase: str) -> str:
    """Geef 'hard' of 'soft' afhankelijk van de fase-eigenschap."""
    if phase in HARD_GATES:
        return "hard"
    if phase in SOFT_GATES:
        return "soft"
    return "soft"


def compute_next(state: dict[str, Any], post_dir: str) -> dict[str, Any]:
    """Bereken de eerstvolgende toegestane actie en agent_brief."""
    phase = state["phase"]
    status = state["status"]

    if phase == "done" or status == "done":
        return {"action": "none", "summary": "Pipeline done.", "agent_brief": None}

    if status == "blocked":
        return {
            "action": "unblock",
            "summary": f"Herstel blocked_reason en complete/reject: {state.get('blocked_reason')}",
            "agent_brief": None,
        }

    if status == "waiting_gate":
        pending = state["gate"].get("pending") or phase
        gtype = gate_type(pending)
        extra = ""
        if pending == "deploy" or phase == "deploy":
            extra = " Voor deploy: approve --deploy zet deploy_approved."
        return {
            "action": "approve_or_reject",
            "phase": pending,
            "gate_type": gtype,
            "summary": f"Gate na {pending} ({gtype}). approve of reject.{extra}",
            "agent_brief": None,
        }

    if status == "running":
        return {
            "action": "complete",
            "phase": phase,
            "summary": f"Content-stap {phase} afronden → complete {phase}",
            "agent_brief": agent_brief(phase, post_dir, state),
        }

    if status == "ready":
        if phase == "intake":
            return {
                "action": "approve",
                "phase": "intake",
                "summary": "Intake bevestigen (approve) → outline ready",
                "agent_brief": None,
            }
        if phase in RUNNABLE:
            if phase == "synthesis" and state["flags"].get("skip_synthesis"):
                return {
                    "action": "approve_skip",
                    "summary": "skip_synthesis aan: set phase visuals via approve path — run set-flag is al gezet; gebruik repair of advance",
                    "agent_brief": None,
                }
            if phase == "deploy" and not state["flags"].get("deploy_approved"):
                return {
                    "action": "approve_deploy_first",
                    "phase": "deploy",
                    "summary": (
                        "deploy vereist deploy_approved: run `approve --deploy` "
                        "voordat je `run deploy` aanroept."
                    ),
                    "agent_brief": None,
                }
            return {
                "action": "run",
                "phase": phase,
                "summary": f"Voer uit: run {phase}",
                "agent_brief": agent_brief(phase, post_dir, state),
            }

    return {"action": "unknown", "summary": f"Geen actie voor {phase}/{status}", "agent_brief": None}


def _precheck_run_clean(phase: str, state: dict[str, Any], post_dir: str) -> list[str]:
    """Prechecks vóór het starten van een 'run <phase>'."""
    errors: list[str] = []
    if phase not in RUNNABLE:
        return [f"Phase '{phase}' is niet runnable."]
    if state["phase"] == "done" or state["status"] == "done":
        return ["Pipeline is done; geen run meer."]
    if state["status"] == "blocked":
        return [f"Status blocked: {state.get('blocked_reason') or 'geen reden'}. Eerst herstellen."]

    defer_visuals = (
        phase == "visuals"
        and state["flags"].get("defer_critique")
        and state["phase"] in {"critique", "synthesis", "visuals"}
    )

    if state["status"] == "waiting_gate" and not defer_visuals:
        return ["Wacht op gate (approve/reject); run is niet toegestaan."]

    if not defer_visuals and state["phase"] != phase:
        return [f"Phase is '{state['phase']}', gevraagd run '{phase}'."]

    if not defer_visuals and state["status"] not in {"ready", "running"}:
        return [f"Status '{state['status']}' laat run niet toe."]

    probed = probe_artefacts(post_dir)

    if phase == "outline":
        pass
    elif phase == "draft":
        if probed["outline"] != "present":
            errors.append("outline.md ontbreekt of is leeg.")
    elif phase in {"style", "series", "critique", "visuals", "deploy"}:
        if probed["draft"] != "present":
            errors.append("draft.md ontbreekt of is leeg.")
    elif phase == "synthesis":
        if state["flags"].get("skip_synthesis"):
            errors.append("skip_synthesis staat aan; synthesis wordt overgeslagen.")
        if probed["grok_feedback"] != "present":
            errors.append("grok-feedback.md ontbreekt of is leeg.")
        if probed["draft"] != "present":
            errors.append("draft.md ontbreekt of is leeg.")

    if phase == "visuals":
        critique_done = probed["grok_feedback"] == "present"
        if not critique_done and not state["flags"].get("defer_critique"):
            errors.append(
                "visuals vereist grok-feedback.md of flags.defer_critique=true."
            )

    if phase == "deploy":
        if not state["flags"].get("deploy_approved"):
            errors.append(
                "deploy vereist flags.deploy_approved=true "
                "(eerst: approve --deploy of set-flag deploy_approved true)."
            )
        if probed["draft"] != "present":
            errors.append("draft.md ontbreekt of is leeg.")
        if probed["factcheck"] != "present" and not state["flags"].get("skip_factcheck"):
            errors.append(
                "feitencheck.md ontbreekt. Publiceren zonder broncontrole is hoe een "
                "verzonnen citaat live kwam te staan (deel 1, augustus 2026). Draai eerst "
                "de factcheck-fase, of zet set-flag skip_factcheck true."
            )

    return errors


def postcheck_complete(
    phase: str,
    state: dict[str, Any],
    post_dir: str,
    post_id: int | None = None,
    edit_url: str | None = None,
) -> list[str]:
    """Postchecks vóór het afronden van 'complete <phase>'."""
    errors: list[str] = []
    probed = probe_artefacts(post_dir)

    if phase == "outline" and probed["outline"] != "present":
        errors.append("outline.md ontbreekt of is leeg.")
    elif phase == "draft" and probed["draft"] != "present":
        errors.append("draft.md ontbreekt of is leeg.")
    elif phase in {"style", "series"}:
        if probed["draft"] != "present":
            errors.append("draft.md ontbreekt of is leeg na style/series.")
    elif phase == "critique" and probed["grok_feedback"] != "present":
        errors.append("grok-feedback.md ontbreekt of is leeg.")
    elif phase == "synthesis" and probed["synthese"] != "present":
        errors.append("synthese.md ontbreekt of is leeg.")
    elif phase == "factcheck" and probed["factcheck"] != "present":
        errors.append(
            "feitencheck.md ontbreekt of is leeg. De bron-check legt elk citaat naast de "
            "bron; zonder dat rapport gaat er niets naar publicatie. Wil je hem echt "
            "overslaan, gebruik dan expliciet: set-flag skip_factcheck true."
        )
    elif phase == "visuals" and probed["visuals"] != "present":
        errors.append(
            f"minder dan {MIN_VISUALS} visuals gevonden "
            f"(nu: {count_visuals(post_dir)}). Elke post krijgt er minimaal "
            f"{MIN_VISUALS}; zie reference/huisstijl.md en de blogpost-visuals-agent."
        )
    elif phase == "deploy":
        pid = post_id or state["artefacts"].get("wp_post_id")
        eurl = edit_url or state["artefacts"].get("edit_url")
        if not pid:
            errors.append("complete deploy vereist --post-id (of reeds gezet in state).")
        if not eurl:
            errors.append("complete deploy vereist --edit-url (of reeds gezet in state).")
        if not state["flags"].get("deploy_approved"):
            errors.append("deploy_approved is false.")
    return errors


def apply_approve_advance(state: dict[str, Any], note: str | None = None, deploy: bool = False) -> None:
    """Keur gate goed en schuif door naar de volgende fase."""
    phase = state["phase"]
    if deploy:
        state["flags"]["deploy_approved"] = True
    state["gate"]["last_decision"] = {
        "at": now_iso(),
        "decision": "approve",
        "phase": phase,
        "note": note,
    }
    state["gate"]["pending"] = None
    state["blocked_reason"] = None
    append_log(state, "gate_approved", note=note, phase=phase)

    if phase == "intake":
        state["phase"] = "outline"
        state["status"] = "ready"
        return

    if phase == "deploy":
        state["phase"] = "done"
        state["status"] = "done"
        return

    nxt = next_phase_after(phase, state["flags"])
    if nxt == "synthesis" and state["flags"].get("skip_synthesis"):
        nxt = "visuals"
    state["phase"] = nxt
    state["status"] = "ready" if nxt != "done" else "done"


def maybe_yolo_approve(state: dict[str, Any], completed_phase: str) -> bool:
    """Return True if yolo auto-approved."""
    if not state.get("yolo_mode"):
        return False
    if gate_type(completed_phase) != "soft":
        return False
    apply_approve_advance(state, note="yolo auto-approve (soft gate)")
    return True
