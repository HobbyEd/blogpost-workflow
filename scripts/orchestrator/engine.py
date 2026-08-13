"""State machine transitielogica en pre/postchecks voor de blogpost workflow."""

from __future__ import annotations

from typing import Any

from .briefs import agent_brief
from .constants import (
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
    if phase in {"deploy", "done"}:
        return "done"

    try:
        current_index = PHASES.index(phase)
    except ValueError:
        raise ValueError(f"Onbekende phase: {phase}") from None

    next_index = current_index + 1
    if next_index >= len(PHASES):
        return "done"

    next_phase = PHASES[next_index]
    return "outline" if next_phase == "intake" else next_phase


def gate_type(phase: str) -> str:
    """Geef 'hard' of 'soft' afhankelijk van de fase-eigenschap."""
    if phase in HARD_GATES:
        return "hard"
    return "soft"


def compute_next(state: dict[str, Any], post_dir: str) -> dict[str, Any]:
    """Bereken de eerstvolgende toegestane actie en agent_brief met schone guard clauses."""
    phase = state["phase"]
    status = state["status"]

    if phase == "done" or status == "done":
        return {"action": "none", "summary": "Pipeline done.", "agent_brief": None}

    if status == "blocked":
        reason = state.get("blocked_reason") or "geen reden"
        return {
            "action": "unblock",
            "summary": f"Herstel blocked_reason en complete/reject: {reason}",
            "agent_brief": None,
        }

    if status == "waiting_gate":
        return _compute_next_for_waiting_gate(state, phase)

    if status == "running":
        return {
            "action": "complete",
            "phase": phase,
            "summary": f"Content-stap {phase} afronden → complete {phase}",
            "agent_brief": agent_brief(phase, post_dir, state),
        }

    if status == "ready":
        return _compute_next_for_ready_status(state, phase, post_dir)

    return {"action": "unknown", "summary": f"Geen actie voor {phase}/{status}", "agent_brief": None}


def _compute_next_for_waiting_gate(state: dict[str, Any], phase: str) -> dict[str, Any]:
    """Helper voor 'waiting_gate' status acties."""
    pending = state["gate"].get("pending") or phase
    gtype = gate_type(pending)
    extra = " Voor deploy: approve --deploy zet deploy_approved." if pending == "deploy" or phase == "deploy" else ""
    return {
        "action": "approve_or_reject",
        "phase": pending,
        "gate_type": gtype,
        "summary": f"Gate na {pending} ({gtype}). approve of reject.{extra}",
        "agent_brief": None,
    }


def _compute_next_for_ready_status(state: dict[str, Any], phase: str, post_dir: str) -> dict[str, Any]:
    """Helper voor 'ready' status acties."""
    if phase == "intake":
        return {
            "action": "approve",
            "phase": "intake",
            "summary": "Intake bevestigen (approve) → outline ready",
            "agent_brief": None,
        }

    if phase not in RUNNABLE:
        return {"action": "unknown", "summary": f"Geen actie voor {phase}/ready", "agent_brief": None}

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
            "summary": "deploy vereist deploy_approved: run `approve --deploy` voordat je `run deploy` aanroept.",
            "agent_brief": None,
        }

    return {
        "action": "run",
        "phase": phase,
        "summary": f"Voer uit: run {phase}",
        "agent_brief": agent_brief(phase, post_dir, state),
    }


def _precheck_run_clean(phase: str, state: dict[str, Any], post_dir: str) -> list[str]:
    """Prechecks vóór het starten van een 'run <phase>' met platte guard clauses."""
    if phase not in RUNNABLE:
        return [f"Phase '{phase}' is niet runnable."]
    if state["phase"] == "done" or state["status"] == "done":
        return ["Pipeline is done; geen run meer."]
    if state["status"] == "blocked":
        reason = state.get("blocked_reason") or "geen reden"
        return [f"Status blocked: {reason}. Eerst herstellen."]

    defer_visuals = _is_defer_visuals_active(phase, state)

    if state["status"] == "waiting_gate" and not defer_visuals:
        return ["Wacht op gate (approve/reject); run is niet toegestaan."]
    if not defer_visuals and state["phase"] != phase:
        return [f"Phase is '{state['phase']}', gevraagd run '{phase}'."]
    if not defer_visuals and state["status"] not in {"ready", "running"}:
        return [f"Status '{state['status']}' laat run niet toe."]

    probed = probe_artefacts(post_dir)
    return _check_run_phase_artefact_requirements(phase, state, probed)


def _is_defer_visuals_active(phase: str, state: dict[str, Any]) -> bool:
    """Controleert of visuals mag draaien onder de defer_critique uitzondering."""
    return (
        phase == "visuals"
        and bool(state["flags"].get("defer_critique"))
        and state["phase"] in {"critique", "synthesis", "visuals"}
    )


def _check_run_phase_artefact_requirements(phase: str, state: dict[str, Any], probed: dict[str, str]) -> list[str]:
    """Controleert specifieke artefact-vereisten per fase vóór het starten van 'run'."""
    errors: list[str] = []

    if phase == "draft" and probed["outline"] != "present":
        errors.append("outline.md ontbreekt of is leeg.")

    if phase in {"style", "series", "critique", "visuals", "deploy"} and probed["draft"] != "present":
        errors.append("draft.md ontbreekt of is leeg.")

    if phase == "synthesis":
        if state["flags"].get("skip_synthesis"):
            errors.append("skip_synthesis staat aan; synthesis wordt overgeslagen.")
        if probed["grok_feedback"] != "present":
            errors.append("grok-feedback.md ontbreekt of is leeg.")
        if probed["draft"] != "present":
            errors.append("draft.md ontbreekt of is leeg.")

    if phase == "visuals":
        critique_done = probed["grok_feedback"] == "present"
        if not critique_done and not state["flags"].get("defer_critique"):
            errors.append("visuals vereist grok-feedback.md of flags.defer_critique=true.")

    if phase == "deploy":
        if not state["flags"].get("deploy_approved"):
            errors.append("deploy vereist flags.deploy_approved=true (eerst: approve --deploy of set-flag deploy_approved true).")
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
    """Postchecks vóór het afronden van 'complete <phase>' met schone dispatcher."""
    probed = probe_artefacts(post_dir)
    errors: list[str] = []

    # Map van fases naar hun specifieke validatiefunctie
    phase_validators = {
        "outline": lambda: ["outline.md ontbreekt of is leeg."] if probed["outline"] != "present" else [],
        "draft": lambda: ["draft.md ontbreekt of is leeg."] if probed["draft"] != "present" else [],
        "style": lambda: ["draft.md ontbreekt of is leeg na style/series."] if probed["draft"] != "present" else [],
        "series": lambda: ["draft.md ontbreekt of is leeg na style/series."] if probed["draft"] != "present" else [],
        "critique": lambda: ["grok-feedback.md ontbreekt of is leeg."] if probed["grok_feedback"] != "present" else [],
        "synthesis": lambda: ["synthese.md ontbreekt of is leeg."] if probed["synthese"] != "present" else [],
        "factcheck": lambda: (
            [
                "feitencheck.md ontbreekt of is leeg. De bron-check legt elk citaat naast de "
                "bron; zonder dat rapport gaat er niets naar publicatie. Wil je hem echt "
                "overslaan, gebruik dan expliciet: set-flag skip_factcheck true."
            ]
            if probed["factcheck"] != "present"
            else []
        ),
        "visuals": lambda: (
            [
                f"minder dan {MIN_VISUALS} visuals gevonden "
                f"(nu: {count_visuals(post_dir)}). Elke post krijgt er minimaal "
                f"{MIN_VISUALS}; zie reference/huisstijl.md en de blogpost-visuals-agent."
            ]
            if probed["visuals"] != "present"
            else []
        ),
        "alignment": lambda: (
            ["archief-consistentie.md ontbreekt of is leeg. Voer de Archief Alignment Check uit (ADR-009)."]
            if probed.get("alignment") != "present"
            else []
        ),
        "deploy": lambda: _validate_deploy_completion(state, post_id, edit_url),
    }

    validator = phase_validators.get(phase)
    if validator:
        errors.extend(validator())

    return errors


def _validate_deploy_completion(state: dict[str, Any], post_id: int | None, edit_url: str | None) -> list[str]:
    """Valideert vereisten voor het afronden van de deploy fase."""
    errors: list[str] = []
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
    """Keur gate goed en schuif door naar de volgende fase met schone flow."""
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
    """Return True indien yolo soft gate auto-approved."""
    if not state.get("yolo_mode") or gate_type(completed_phase) != "soft":
        return False

    apply_approve_advance(state, note="yolo auto-approve (soft gate)")
    return True
