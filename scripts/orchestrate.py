#!/usr/bin/env python3
"""Strikte control plane voor de blogpost-workflow.

Fasevolgorde, pre/postconditions, gates en named exceptions zitten hier —
niet in een LLM-skill. Content-agents draaien buiten dit script; dit script
zegt wat mag, controleert artefacten en houdt state.json bij.

Zie ontwerp-strikte-orkestrator.md.

Gebruik:
    python3 scripts/orchestrate.py init --slug S --titel T
    python3 scripts/orchestrate.py status --post S
    python3 scripts/orchestrate.py next --post S
    python3 scripts/orchestrate.py run outline --post S
    python3 scripts/orchestrate.py complete outline --post S
    python3 scripts/orchestrate.py approve --post S --note "ok"
    python3 scripts/orchestrate.py doctor --post S
    python3 scripts/orchestrate.py import-md --post S

Exitcodes: 0 ok, 1 usage/IO, 2 illegale transitie of pre/post-fout, 3 doctor hard fail.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any

# --------------------------- constants ---------------------------

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
HARD_GATES = {"synthesis", "factcheck", "deploy", "intake"}

STATUSES = {"ready", "running", "waiting_gate", "blocked", "done"}

ARTEFACT_FILES = {
    "outline": "outline.md",
    "draft": "draft.md",
    "grok_feedback": "grok-feedback.md",
    "synthese": "synthese.md",
    "factcheck": "feitencheck.md",
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
    "deploy": "6 Deploy (concept)",
    "done": "Klaar",
}


# --------------------------- paths ---------------------------

def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def posts_root() -> str:
    return os.path.join(repo_root(), "posts")


def resolve_post_dir(post: str | None, post_dir: str | None) -> str:
    if post_dir:
        path = os.path.abspath(post_dir)
    elif post:
        path = os.path.join(posts_root(), post)
    else:
        raise SystemExit("Geef --post <slug> of --post-dir <pad>.")
    return path


def state_path(post_dir: str) -> str:
    return os.path.join(post_dir, "state.json")


# --------------------------- time / io ---------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today() -> str:
    return date.today().isoformat()


def load_state(post_dir: str) -> dict[str, Any]:
    path = state_path(post_dir)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Geen state.json in {post_dir}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return normalize_state(data)


def save_state(post_dir: str, state: dict[str, Any]) -> None:
    path = state_path(post_dir)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def append_log(state: dict[str, Any], event: str, note: str | None = None, phase: str | None = None) -> None:
    entry: dict[str, Any] = {"at": now_iso(), "event": event}
    if phase is not None:
        entry["phase"] = phase
    elif state.get("phase"):
        entry["phase"] = state["phase"]
    if note:
        entry["note"] = note
    state.setdefault("log", []).append(entry)


def empty_state(slug: str, titel: str, yolo: bool = False) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "slug": slug,
        "titel": titel,
        "aangemaakt": today(),
        "yolo_mode": bool(yolo),
        "phase": "outline",
        "status": "ready",
        "artefacts": {
            "outline": "missing",
            "draft": "missing",
            "grok_feedback": "missing",
            "synthese": "missing",
            "visuals": "missing",
            "wp_post_id": None,
            "edit_url": None,
        },
        "flags": {
            "skip_synthesis": False,
            "skip_factcheck": False,
            "defer_critique": False,
            "deploy_approved": False,
        },
        "gate": {"pending": None, "last_decision": None},
        "blocked_reason": None,
        "log": [
            {
                "at": now_iso(),
                "event": "intake_completed",
                "phase": "intake",
                "note": "map en state.json aangemaakt",
            }
        ],
    }


def normalize_state(data: dict[str, Any]) -> dict[str, Any]:
    """Vul ontbrekende defaults; gooi geen stille fase-wijzigingen."""
    base = empty_state(data.get("slug") or "unknown", data.get("titel") or "")
    out = deepcopy(base)
    out.update({k: data[k] for k in data if k not in ("artefacts", "flags", "gate", "log")})
    out["artefacts"] = {**base["artefacts"], **(data.get("artefacts") or {})}
    out["flags"] = {**base["flags"], **(data.get("flags") or {})}
    out["gate"] = {**base["gate"], **(data.get("gate") or {})}
    out["log"] = list(data.get("log") or base["log"])
    out["yolo_mode"] = bool(out.get("yolo_mode"))
    for k in FLAG_NAMES:
        out["flags"][k] = bool(out["flags"].get(k))
    if out.get("phase") not in PHASES:
        raise ValueError(f"Ongeldige phase: {out.get('phase')}")
    if out.get("status") not in STATUSES:
        raise ValueError(f"Ongeldige status: {out.get('status')}")
    return out


# --------------------------- filesystem probes ---------------------------

def file_nonempty(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0


IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

# Huisstijl-eis: elke post krijgt minimaal twee visuals. Die ondergrens stond eerder
# alleen in de agent-instructie, waardoor `complete visuals` met een enkele visual slaagde.
MIN_VISUALS = 2


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
    return count_local_visuals(post_dir) > 0


def has_image_refs(post_dir: str) -> bool:
    """Beeldverwijzingen in draft.md tellen ook als visual.

    Een recap of vervolgdeel mag al gepubliceerde media hergebruiken via een
    absolute URL. Dan staan er geen bestanden in visuals/, maar is de
    visuals-stap wel degelijk uitgevoerd en reviewbaar.
    """
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
    """Aantal visuals bij deze post: het hoogste van bestanden en verwijzingen.

    Hergebruikte media staan alleen als verwijzing in de draft, eigen visuals staan
    ook op schijf. Het maximum voorkomt dubbeltellen wanneer beide er zijn.
    """
    return max(count_local_visuals(post_dir), count_image_refs(post_dir))


def has_visuals(post_dir: str) -> bool:
    return count_visuals(post_dir) >= MIN_VISUALS


def probe_artefacts(post_dir: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, fname in ARTEFACT_FILES.items():
        out[key] = "present" if file_nonempty(os.path.join(post_dir, fname)) else "missing"
    out["visuals"] = "present" if has_visuals(post_dir) else "missing"
    return out


def sync_artefact_flags(state: dict[str, Any], post_dir: str) -> None:
    probed = probe_artefacts(post_dir)
    for k, v in probed.items():
        state["artefacts"][k] = v
    # keep wp fields as stored


# --------------------------- transitions ---------------------------

def next_phase_after(phase: str, flags: dict[str, Any]) -> str:
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
    # skip intake when advancing from synthetic positions
    if nxt == "intake":
        nxt = "outline"
    return nxt


def gate_type(phase: str) -> str:
    if phase in HARD_GATES:
        return "hard"
    if phase in SOFT_GATES:
        return "soft"
    return "soft"


def agent_brief(phase: str, post_dir: str, state: dict[str, Any]) -> dict[str, Any]:
    slug = state.get("slug") or os.path.basename(post_dir.rstrip("/"))
    rel = f"posts/{slug}"
    common = {
        "agent": AGENT_FOR_PHASE.get(phase),
        "phase": phase,
        "post_dir": rel,
        "slug": slug,
    }
    briefs = {
        "outline": {
            **common,
            "inputs": ["onderwerp/titel", "backlog of brainstorm indien genoemd"],
            "outputs": [f"{rel}/outline.md"],
            "instruction": (
                "Roep blogpost-onderzoeker aan. Schrijf een compacte outline met bronnen "
                f"(URL's geverifieerd) naar {rel}/outline.md. Verzin geen fase; alleen outline."
            ),
        },
        "draft": {
            **common,
            "inputs": [f"{rel}/outline.md", "reference/huisstijl.md"],
            "outputs": [f"{rel}/draft.md"],
            "instruction": (
                "Roep blogpost-schrijver aan. Schrijf draft.md in huisstijl op basis van outline.md. "
                "Geen feiten buiten de outline."
            ),
        },
        "style": {
            **common,
            "inputs": [f"{rel}/draft.md", "reference/huisstijl.md"],
            "outputs": ["rapport aan orkestrator/host (geen file verplicht)"],
            "instruction": (
                "Roep stijl-check aan op draft.md. Rapporteer alleen; pas de draft niet zelf aan. "
                "Leg het rapport vast in de gate-notitie bij approve/reject."
            ),
        },
        "series": {
            **common,
            "inputs": [f"{rel}/draft.md", "posts/*/"],
            "outputs": ["rapport aan orkestrator/host"],
            "instruction": (
                "Roep reeks-consistentie-check aan. Vergelijk met eerdere delen in posts/*/. "
                "Rapporteer alleen; pas de draft niet zelf aan."
            ),
        },
        "critique": {
            **common,
            "inputs": [f"{rel}/draft.md"],
            "outputs": [f"{rel}/grok-feedback.md"],
            "instruction": (
                "Roep grok-reviewer aan (Grok-MCP). Schrijf ruwe kritiek naar grok-feedback.md. "
                "Verzin geen kritiek als de tool faalt — laat complete falen."
            ),
        },
        "synthesis": {
            **common,
            "inputs": [f"{rel}/draft.md", f"{rel}/grok-feedback.md"],
            "outputs": [f"{rel}/synthese.md"],
            "instruction": (
                "Roep blogpost-onderzoeker aan voor synthese: weeg Grok-punten, schrijf "
                "aanpasvoorstel naar synthese.md. Herschrijf draft.md niet in deze stap."
            ),
        },
        "visuals": {
            **common,
            "inputs": [f"{rel}/draft.md", "reference/huisstijl.md"],
            "outputs": [f"{rel}/visuals/", "beeldrefs in draft.md"],
            "instruction": (
                "Roep blogpost-visuals aan. Spaarzame SVG's, render via scripts/render_svg.py, "
                "zet ![alt](visuals/....png) in draft.md."
            ),
        },
        "factcheck": {
            **common,
            "inputs": [f"{rel}/draft.md"],
            "outputs": [f"{rel}/feitencheck.md"],
            "instruction": (
                "Roep bron-check aan. Elk citaat en elke bron in draft.md tegen de bron "
                "leggen; niets aannemen op gezag van de outline. Rapport naar "
                f"{rel}/feitencheck.md. Dit is de laatste controle voor publicatie."
            ),
        },
        "deploy": {
            **common,
            "inputs": [f"{rel}/draft.md", f"{rel}/visuals/"],
            "outputs": ["WordPress concept (post_id, edit_url)"],
            "instruction": (
                "Alleen na deploy_approved. Roep blogpost-deploy / "
                f"python3 scripts/deploy_post.py --post-dir {rel} aan. "
                "Daarna: orchestrate.py complete deploy --post-id N --edit-url URL."
            ),
        },
    }
    return briefs.get(phase, {**common, "instruction": f"Voer phase {phase} uit."})


def _precheck_run_clean(phase: str, state: dict[str, Any], post_dir: str) -> list[str]:
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


def postcheck_complete(phase: str, state: dict[str, Any], post_dir: str, args: argparse.Namespace) -> list[str]:
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
        post_id = getattr(args, "post_id", None) or state["artefacts"].get("wp_post_id")
        edit_url = getattr(args, "edit_url", None) or state["artefacts"].get("edit_url")
        if not post_id:
            errors.append("complete deploy vereist --post-id (of reeds gezet in state).")
        if not edit_url:
            errors.append("complete deploy vereist --edit-url (of reeds gezet in state).")
        if not state["flags"].get("deploy_approved"):
            errors.append("deploy_approved is false.")
    return errors


# --------------------------- commands ---------------------------

def cmd_init(args: argparse.Namespace) -> int:
    slug = args.slug.strip()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        print("Slug moet kebab-case zijn: [a-z0-9]+(-[a-z0-9]+)*", file=sys.stderr)
        return 1
    post_dir = os.path.join(posts_root(), slug)
    os.makedirs(post_dir, exist_ok=True)
    path = state_path(post_dir)
    if os.path.isfile(path) and not args.force:
        print(f"state.json bestaat al: {path} (gebruik --force om te overschrijven)", file=sys.stderr)
        return 1
    state = empty_state(slug, args.titel, yolo=args.yolo)
    if args.wait_intake_gate:
        state["phase"] = "intake"
        state["status"] = "waiting_gate"
        state["gate"]["pending"] = "intake"
    save_state(post_dir, state)
    print(json.dumps({"ok": True, "post_dir": post_dir, "state": state}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    state = load_state(post_dir)
    sync_artefact_flags(state, post_dir)
    action = compute_next(state, post_dir)
    out = {
        "post_dir": post_dir,
        "slug": state["slug"],
        "titel": state["titel"],
        "phase": state["phase"],
        "phase_label": PHASE_LABELS.get(state["phase"], state["phase"]),
        "status": state["status"],
        "yolo_mode": state["yolo_mode"],
        "flags": state["flags"],
        "gate": state["gate"],
        "blocked_reason": state.get("blocked_reason"),
        "artefacts": state["artefacts"],
        "next": action,
    }
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Post:     {state['slug']}")
        print(f"Titel:    {state['titel']}")
        print(f"Phase:    {state['phase']} ({PHASE_LABELS.get(state['phase'], '')})")
        print(f"Status:   {state['status']}")
        print(f"Yolo:     {state['yolo_mode']}")
        print(f"Flags:    {json.dumps(state['flags'], ensure_ascii=False)}")
        print(f"Gate:     {json.dumps(state['gate'], ensure_ascii=False)}")
        if state.get("blocked_reason"):
            print(f"Blocked:  {state['blocked_reason']}")
        print(f"Artefacts:{json.dumps(state['artefacts'], ensure_ascii=False)}")
        print(f"Next:     {action.get('action')} — {action.get('summary')}")
    return 0


def compute_next(state: dict[str, Any], post_dir: str) -> dict[str, Any]:
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
            # synthesis skip
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


# --------------------------- status table (derived, not stored) ---------------------------

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
    """Bereken de statustabel puur uit state.json + bestanden op schijf.

    Geen apart opgeslagen tabel: dit is exact het mechanisme dat state.md liet
    driften (huidige_fase vs. fasentabel vs. schijf raakten los van elkaar).
    """
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


def cmd_table(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    state = load_state(post_dir)
    sync_artefact_flags(state, post_dir)
    rows = build_phase_table(state, post_dir)
    if args.json:
        print(json.dumps({"slug": state["slug"], "titel": state["titel"], "rows": rows}, ensure_ascii=False, indent=2))
    else:
        print(render_phase_table_md(state, rows))
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    state = load_state(post_dir)
    sync_artefact_flags(state, post_dir)
    action = compute_next(state, post_dir)
    print(json.dumps(action, ensure_ascii=False, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    phase = args.phase
    state = load_state(post_dir)
    errors = _precheck_run_clean(phase, state, post_dir)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    # defer_critique visuals: temporarily move phase if needed
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
    sync_artefact_flags(state, post_dir)
    save_state(post_dir, state)

    brief = agent_brief(phase, post_dir, state)
    print(
        json.dumps(
            {
                "ok": True,
                "phase": phase,
                "status": "running",
                "agent_brief": brief,
                "note": "Voer de agent/script uit; daarna: complete " + phase,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def apply_approve_advance(state: dict[str, Any], note: str | None, deploy: bool = False) -> None:
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
    # skip synthesis phase entry if flag set and we're leaving critique — handled in next_phase_after
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


def cmd_complete(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    phase = args.phase
    state = load_state(post_dir)

    if state["status"] not in {"running", "ready", "blocked"}:
        # allow complete from ready only if artefact already there (import recovery)
        if state["status"] != "waiting_gate":
            pass
    if state["phase"] != phase and not (
        phase == "visuals" and state["flags"].get("defer_critique")
    ):
        print(
            json.dumps(
                {
                    "ok": False,
                    "errors": [f"Phase is '{state['phase']}', complete '{phase}' geweigerd."],
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    if state["status"] == "waiting_gate" and state["phase"] == phase:
        print(
            json.dumps(
                {"ok": False, "errors": ["Al waiting_gate; gebruik approve/reject."]},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    errors = postcheck_complete(phase, state, post_dir, args)
    if errors:
        state["status"] = "blocked"
        state["blocked_reason"] = "; ".join(errors)
        append_log(state, "complete_failed", note=state["blocked_reason"], phase=phase)
        save_state(post_dir, state)
        print(json.dumps({"ok": False, "errors": errors, "status": "blocked"}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    # store deploy artefacts
    if phase == "deploy":
        if args.post_id:
            state["artefacts"]["wp_post_id"] = args.post_id
        if args.edit_url:
            state["artefacts"]["edit_url"] = args.edit_url

    sync_artefact_flags(state, post_dir)
    state["phase"] = phase
    state["blocked_reason"] = None
    append_log(state, "complete_ok", phase=phase)

    yolo_advanced = maybe_yolo_approve(state, phase)
    if not yolo_advanced:
        state["status"] = "waiting_gate"
        state["gate"]["pending"] = phase

    save_state(post_dir, state)
    print(
        json.dumps(
            {
                "ok": True,
                "phase": state["phase"],
                "status": state["status"],
                "yolo_advanced": yolo_advanced,
                "gate": state["gate"],
                "next": compute_next(state, post_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    state = load_state(post_dir)

    if args.deploy:
        state["flags"]["deploy_approved"] = True
        append_log(state, "deploy_approved_set", note=args.note)
        # If currently ready on deploy, stay ready for run
        if state["phase"] == "deploy" and state["status"] == "ready":
            save_state(post_dir, state)
            print(json.dumps({"ok": True, "flags": state["flags"], "next": compute_next(state, post_dir)}, ensure_ascii=False, indent=2))
            return 0

    if state["status"] != "waiting_gate" and state["phase"] != "intake":
        # Allow approve on intake ready/waiting
        if not (state["phase"] == "intake" and state["status"] in {"ready", "waiting_gate"}):
            # Special: after setting deploy_approved only
            if args.deploy and state["status"] != "waiting_gate":
                save_state(post_dir, state)
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "note": "deploy_approved gezet; pipeline-gate niet van toepassing",
                            "flags": state["flags"],
                            "next": compute_next(state, post_dir),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            print(
                json.dumps(
                    {
                        "ok": False,
                        "errors": [f"Approve alleen bij waiting_gate (nu: {state['status']})."],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 2

    if state["phase"] == "deploy" and state["status"] == "waiting_gate":
        # approving deploy gate means concept is accepted → done
        if not state["flags"].get("deploy_approved") and not args.deploy:
            state["flags"]["deploy_approved"] = True
        apply_approve_advance(state, args.note, deploy=True)
    else:
        apply_approve_advance(state, args.note, deploy=args.deploy)

    # If we landed on synthesis but skip is on, jump
    if state["phase"] == "synthesis" and state["flags"].get("skip_synthesis"):
        state["phase"] = "visuals"
        append_log(state, "skip_synthesis_applied", note="phase → visuals")

    sync_artefact_flags(state, post_dir)
    save_state(post_dir, state)
    print(
        json.dumps(
            {
                "ok": True,
                "phase": state["phase"],
                "status": state["status"],
                "next": compute_next(state, post_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    state = load_state(post_dir)
    if state["status"] not in {"waiting_gate", "blocked", "running"}:
        print(
            json.dumps(
                {"ok": False, "errors": [f"Reject niet zinvol bij status {state['status']}."]},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    phase = state["gate"].get("pending") or state["phase"]
    state["gate"]["last_decision"] = {
        "at": now_iso(),
        "decision": "reject",
        "phase": phase,
        "note": args.note,
    }
    state["gate"]["pending"] = None
    state["status"] = "ready"
    state["phase"] = phase if phase in PHASES else state["phase"]
    state["blocked_reason"] = None
    append_log(state, "gate_rejected", note=args.note, phase=phase)
    save_state(post_dir, state)
    print(
        json.dumps(
            {
                "ok": True,
                "phase": state["phase"],
                "status": "ready",
                "next": compute_next(state, post_dir),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_set_flag(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    state = load_state(post_dir)
    name = args.name
    if name == "yolo_mode":
        state["yolo_mode"] = args.value
        append_log(state, "flag_set", note=f"yolo_mode={args.value}")
    elif name in FLAG_NAMES:
        state["flags"][name] = args.value
        append_log(state, "flag_set", note=f"{name}={args.value}")
    else:
        print(f"Onbekende flag: {name}. Kies: yolo_mode, {', '.join(FLAG_NAMES)}", file=sys.stderr)
        return 1
    save_state(post_dir, state)
    print(json.dumps({"ok": True, "yolo_mode": state["yolo_mode"], "flags": state["flags"]}, ensure_ascii=False, indent=2))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    issues: list[dict[str, str]] = []
    hard = 0

    if not os.path.isdir(post_dir):
        print(json.dumps({"ok": False, "errors": [f"Map ontbreekt: {post_dir}"]}, indent=2), file=sys.stderr)
        return 1

    has_json = os.path.isfile(state_path(post_dir))
    if not has_json:
        issues.append({"severity": "error", "msg": "state.json ontbreekt — run import-md of init"})
        hard += 1
        print(json.dumps({"ok": False, "issues": issues, "probed": probe_artefacts(post_dir)}, ensure_ascii=False, indent=2))
        return 3

    state = load_state(post_dir)
    probed = probe_artefacts(post_dir)

    for key, disk in probed.items():
        stored = state["artefacts"].get(key)
        if stored != disk:
            issues.append(
                {
                    "severity": "warning",
                    "msg": f"artefacts.{key}: state={stored}, disk={disk}",
                }
            )

    # Linear consistency: if later artefact present, earlier should be present.
    # Named exceptions: skip_synthesis (synthese mag missen), defer_critique (visuals vóór
    # critique), skip_factcheck (broncontrole mag missen; nooit stilzwijgend).
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
        # present
        relevant_missing = set(missing_before)
        if key == "visuals" and state["flags"].get("skip_synthesis"):
            relevant_missing.discard("synthese")
        if key == "visuals" and state["flags"].get("defer_critique"):
            # visuals vóór/tijdens open critique is bewust
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

    # Phase vs artefacts
    phase = state["phase"]
    if phase in {"draft", "style", "series", "critique", "synthesis", "visuals", "deploy", "done"}:
        if probed["outline"] != "present":
            issues.append({"severity": "error", "msg": f"phase={phase} maar outline.md mist"})
            hard += 1
    if phase in {"style", "series", "critique", "synthesis", "visuals", "deploy", "done"}:
        if probed["draft"] != "present" and phase != "outline":
            if phase != "draft" or state["status"] != "ready":
                if phase not in {"draft"}:
                    issues.append({"severity": "error", "msg": f"phase={phase} maar draft.md mist"})
                    hard += 1

    if state["artefacts"].get("wp_post_id") and phase not in {"deploy", "done"}:
        issues.append(
            {
                "severity": "warning",
                "msg": f"wp_post_id gezet maar phase={phase} (verwacht deploy/done of named exception)",
            }
        )

    if phase == "done" and not state["artefacts"].get("wp_post_id"):
        issues.append({"severity": "warning", "msg": "phase=done zonder wp_post_id"})

    if state["flags"].get("skip_synthesis") and probed["synthese"] == "present":
        issues.append({"severity": "info", "msg": "skip_synthesis aan maar synthese.md bestaat wel"})

    if state["status"] == "waiting_gate" and not state["gate"].get("pending"):
        issues.append({"severity": "warning", "msg": "waiting_gate zonder gate.pending"})

    if state["status"] == "running":
        issues.append({"severity": "info", "msg": "status=running — complete of reject verwacht"})

    out = {
        "ok": hard == 0,
        "slug": state["slug"],
        "phase": phase,
        "status": state["status"],
        "flags": state["flags"],
        "probed": probed,
        "stored_artefacts": state["artefacts"],
        "issues": issues,
        "next": compute_next(state, post_dir),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if hard == 0 else 3


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

    # Phase status from table rows: | N | Name | status | artefact |
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

    # Map skill phases to machine phases
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

    # Determine furthest gereed and first open/bezig
    order_nums = ["0", "1", "2", "2b", "2c", "3", "4", "5", "6"]
    # Some old tables lack 2c
    present_nums = [n for n in order_nums if row_status(n) is not None]
    if not present_nums:
        present_nums = [n for n in order_nums if n != "2c"]

    current_phase = "outline"
    current_status = "ready"
    skip_synthesis = False
    defer_critique = False

    # Find first not gereed
    first_open = None
    for n in present_nums:
        st = row_status(n)
        if st in {"open", "bezig", "afgekeurd"}:
            first_open = n
            break

    all_gereed = all(row_status(n) == "gereed" for n in present_nums if row_status(n))

    if all_gereed and present_nums:
        # If deploy gereed → done
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
            # open: if previous gereed, ready to run this phase
            current_status = "ready"

    # Drift detection: later gereed while earlier open
    critique_open = row_status("3") in {None, "open", "bezig"}
    visuals_gereed = row_status("5") == "gereed"
    deploy_gereed = row_status("6") == "gereed"
    synthesis_open = row_status("4") in {None, "open", "bezig"}

    if (visuals_gereed or deploy_gereed) and critique_open:
        defer_critique = True
    if deploy_gereed and synthesis_open:
        skip_synthesis = True
    if deploy_gereed and row_status("6") == "gereed":
        # Prefer done if deploy finished even if earlier open in table
        if not critique_open or True:
            # If deploy is gereed, pipeline effectively done for WP purposes
            if deploy_gereed:
                current_phase = "done"
                current_status = "done"

    # Frontmatter huidige_fase override if more specific and table empty-ish
    hf = meta.get("huidige_fase", "")
    # Don't trust stale huidige_fase if deploy gereed
    if deploy_gereed:
        current_phase = "done"
        current_status = "done"

    yolo = meta.get("yolo_mode", "uit").lower() in {"aan", "true", "1", "yes"}

    # WP post id from table artefact cell or body
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


def cmd_import_md(args: argparse.Namespace) -> int:
    post_dir = resolve_post_dir(args.post, args.post_dir)
    md_path = os.path.join(post_dir, "state.md")
    if not os.path.isfile(md_path):
        print(f"Geen state.md in {post_dir}", file=sys.stderr)
        return 1
    if os.path.isfile(state_path(post_dir)) and not args.force:
        print("state.json bestaat al; gebruik --force om te overschrijven", file=sys.stderr)
        return 1

    parsed = parse_state_md(md_path)
    meta = parsed["meta"]
    slug = meta.get("slug") or os.path.basename(post_dir.rstrip("/"))
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

    sync_artefact_flags(state, post_dir)
    # If done, mark all present artefacts
    if state["phase"] == "done":
        state["status"] = "done"

    note = (
        f"import-md uit state.md; huidige_fase_raw={parsed.get('huidige_fase_raw')!r}; "
        f"flags skip_synthesis={state['flags']['skip_synthesis']} "
        f"defer_critique={state['flags']['defer_critique']}"
    )
    append_log(state, "imported_from_md", note=note)
    save_state(post_dir, state)
    print(json.dumps({"ok": True, "state": state, "doctor_hint": "run doctor"}, ensure_ascii=False, indent=2))
    return 0


def cmd_render_md(args: argparse.Namespace) -> int:
    """Schrijf een compacte projectie state.md vanuit state.json (overschrijft niet blind de beslislog)."""
    post_dir = resolve_post_dir(args.post, args.post_dir)
    state = load_state(post_dir)
    sync_artefact_flags(state, post_dir)
    out_path = os.path.join(post_dir, "state.generated.md")
    if args.in_place:
        out_path = os.path.join(post_dir, "state.md")

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
    print(json.dumps({"ok": True, "path": out_path}, ensure_ascii=False, indent=2))
    return 0


def cmd_repair(args: argparse.Namespace) -> int:
    """Herleid phase/status uit artefacten + flags; met --apply schrijven."""
    post_dir = resolve_post_dir(args.post, args.post_dir)
    state = load_state(post_dir)
    probed = probe_artefacts(post_dir)
    proposal = deepcopy(state)

    # Infer furthest complete step
    if probed["outline"] != "present":
        proposal["phase"] = "outline"
        proposal["status"] = "ready"
    elif probed["draft"] != "present":
        proposal["phase"] = "draft"
        proposal["status"] = "ready"
    else:
        # draft exists — style/series have no files; use state or assume ready for style if phase early
        if probed["grok_feedback"] != "present":
            if state["flags"].get("defer_critique") and probed["visuals"] == "present":
                proposal["phase"] = "critique"
                proposal["status"] = "ready"
            else:
                # if was past draft in state, keep series/style heuristics from current
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

    # Prefer wp done
    wp = state["artefacts"].get("wp_post_id")
    if wp:
        proposal["artefacts"]["wp_post_id"] = wp
        proposal["phase"] = "done"
        proposal["status"] = "done"
        proposal["flags"]["deploy_approved"] = True

    sync_artefact_flags(proposal, post_dir)

    out = {
        "current": {"phase": state["phase"], "status": state["status"]},
        "proposal": {"phase": proposal["phase"], "status": proposal["status"], "flags": proposal["flags"]},
        "probed": probed,
        "applied": False,
    }
    if args.apply:
        state["phase"] = proposal["phase"]
        state["status"] = proposal["status"]
        state["flags"] = proposal["flags"]
        sync_artefact_flags(state, post_dir)
        append_log(state, "repair_applied", note=json.dumps(out["proposal"], ensure_ascii=False))
        save_state(post_dir, state)
        out["applied"] = True
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


# --------------------------- argparse ---------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Strikte blogpost-orkestrator (control plane)")
    sub = p.add_subparsers(dest="command", required=True)

    def add_post_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--post", help="Slug onder posts/")
        sp.add_argument("--post-dir", help="Absoluut of relatief pad naar postmap")

    sp = sub.add_parser("init", help="Nieuwe postmap + state.json")
    sp.add_argument("--slug", required=True)
    sp.add_argument("--titel", required=True)
    sp.add_argument("--yolo", action="store_true")
    sp.add_argument("--force", action="store_true")
    sp.add_argument(
        "--wait-intake-gate",
        action="store_true",
        help="Start op intake/waiting_gate i.p.v. outline/ready",
    )

    sp = sub.add_parser("status", help="Toon fase en next action")
    add_post_args(sp)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("table", help="Statustabel per fase, afgeleid uit state.json + schijf")
    add_post_args(sp)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("next", help="Eén toegestane vervolgactie + agent_brief")
    add_post_args(sp)

    sp = sub.add_parser("run", help="Start phase (prechecks → running)")
    add_post_args(sp)
    sp.add_argument("phase", choices=sorted(RUNNABLE))

    sp = sub.add_parser("complete", help="Rond phase af (postchecks → gate of yolo)")
    add_post_args(sp)
    sp.add_argument("phase", choices=sorted(RUNNABLE))
    sp.add_argument("--post-id", type=int, default=None)
    sp.add_argument("--edit-url", default=None)

    sp = sub.add_parser("approve", help="Gate akkoord → volgende phase")
    add_post_args(sp)
    sp.add_argument("--note", default=None)
    sp.add_argument(
        "--deploy",
        action="store_true",
        help="Zet deploy_approved (en approve deploy-gate indien waiting)",
    )

    sp = sub.add_parser("reject", help="Gate afgewezen → opnieuw ready")
    add_post_args(sp)
    sp.add_argument("--note", default=None)

    sp = sub.add_parser("set-flag", help="Zet yolo_mode of named exception")
    add_post_args(sp)
    sp.add_argument("name", choices=["yolo_mode", *FLAG_NAMES])
    sp.add_argument("value", choices=["true", "false"])

    sp = sub.add_parser("doctor", help="Detecteer drift state vs. schijf")
    add_post_args(sp)

    sp = sub.add_parser("import-md", help="Importeer legacy state.md → state.json")
    add_post_args(sp)
    sp.add_argument("--force", action="store_true")

    sp = sub.add_parser("render-md", help="Projectie state.json → state.generated.md")
    add_post_args(sp)
    sp.add_argument("--in-place", action="store_true", help="Schrijf state.md (let op: overschrijft)")

    sp = sub.add_parser("repair", help="Stel phase/status voor op basis van artefacten")
    add_post_args(sp)
    sp.add_argument("--apply", action="store_true")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "set-flag":
        args.value = args.value == "true"

    try:
        if args.command == "init":
            return cmd_init(args)
        if args.command == "status":
            return cmd_status(args)
        if args.command == "table":
            return cmd_table(args)
        if args.command == "next":
            return cmd_next(args)
        if args.command == "run":
            return cmd_run(args)
        if args.command == "complete":
            return cmd_complete(args)
        if args.command == "approve":
            return cmd_approve(args)
        if args.command == "reject":
            return cmd_reject(args)
        if args.command == "set-flag":
            return cmd_set_flag(args)
        if args.command == "doctor":
            return cmd_doctor(args)
        if args.command == "import-md":
            return cmd_import_md(args)
        if args.command == "render-md":
            return cmd_render_md(args)
        if args.command == "repair":
            return cmd_repair(args)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Ongeldige JSON: {e}", file=sys.stderr)
        return 1

    parser.error(f"Onbekend commando: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
