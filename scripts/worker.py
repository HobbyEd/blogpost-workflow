#!/usr/bin/env python3
"""Execution plane: voert één running fase uit via Claude Code.

De control plane (`WorkflowService`) zet een fase op `running` en levert een
`agent_brief`. Deze worker pakt die brief op, draait `claude -p` in de repo, en
roept daarna `complete` aan.

Harde grens (ADR-010): de worker keurt nooit een gate goed. `approve` blijft bij
de auteur in de UI. Alleen fases met `status: running` worden opgepakt.

Gebruik:
    .venv/bin/python scripts/worker.py --once
    .venv/bin/python scripts/worker.py --once --dry-run
    .venv/bin/python scripts/worker.py --once --post <slug>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Callable

# Zelfde importpad als orchestrate.py: scripts/ staat op sys.path.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from orchestrator.repository import now_iso, repo_root
from orchestrator.service import WorkflowService
from orchestrator import worker_status

DEFAULT_TIMEOUT_S = 1800
DEFAULT_CLAUDE = "/Users/evdillen/.local/bin/claude"

POST_ID_RE = re.compile(r'"post_id"\s*:\s*(\d+)')
EDIT_URL_RE = re.compile(r'"edit_url"\s*:\s*"(https?://[^"]+)"')

Runner = Callable[[str, dict[str, Any]], dict[str, Any]]
OnClaim = Callable[[dict[str, Any]], None]


class WorkerError(Exception):
    """Uitvoering van één fase is mislukt."""


class HeartbeatWriter:
    """Houdt het heartbeat-bestand vers zolang dit proces leeft."""

    def __init__(self, interval_s: int = 30, timeout_s: int = DEFAULT_TIMEOUT_S) -> None:
        self.interval_s = interval_s
        self.timeout_s = timeout_s
        self.pid = os.getpid()
        self._lock = threading.Lock()
        self._state = "idle"
        self._job: dict[str, Any] | None = None
        self._started_at: str | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self.flush()
        self._thread = threading.Thread(target=self._loop, name="worker-heartbeat", daemon=True)
        self._thread.start()

    def update(self, state: str, job: dict[str, Any] | None = None) -> None:
        with self._lock:
            same_job = (
                state == "busy"
                and job is not None
                and self._job is not None
                and job.get("slug") == self._job.get("slug")
                and job.get("phase") == self._job.get("phase")
            )
            self._state = state
            self._job = {"slug": job["slug"], "phase": job["phase"]} if job else None
            if state == "busy" and job and not same_job:
                self._started_at = now_iso()
            if state != "busy":
                self._started_at = None
        self.flush()

    def flush(self) -> None:
        with self._lock:
            worker_status.write_heartbeat(
                pid=self.pid,
                state=self._state,
                job=self._job,
                interval_s=self.interval_s,
                timeout_s=self.timeout_s,
                started_at=self._started_at,
            )

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
        worker_status.clear_heartbeat()

    def _loop(self) -> None:
        while not self._stop.wait(10):
            self.flush()


def resolve_claude_bin(explicit: str | None = None) -> str:
    """Vind de Claude Code-binary. Absoluut pad, zodat een kaal PATH geen probleem is."""
    if explicit:
        return explicit
    env = os.environ.get("CLAUDE_BIN")
    if env:
        return env
    found = shutil.which("claude")
    if found:
        return found
    if os.path.isfile(DEFAULT_CLAUDE):
        return DEFAULT_CLAUDE
    raise WorkerError(
        "claude niet gevonden. Installeer Claude Code of geef --claude / CLAUDE_BIN."
    )


def format_prompt(brief: dict[str, Any]) -> str:
    """Zet de agent_brief om in één print-mode prompt.

    De brief is geschreven voor de skill-host ('roep X aan'). In `claude -p`
    ís die host Claude Code zelf, inclusief de subagents in `.claude/agents/`.
    """
    outputs = brief.get("outputs") or []
    inputs = brief.get("inputs") or []
    return (
        "Je voert precies één fase uit van de blogpost-workflow.\n"
        f"Fase: {brief.get('phase')}\n"
        f"Subagent: {brief.get('agent')}\n"
        f"Postmap: {brief.get('post_dir')}\n"
        f"Invoer: {', '.join(inputs) if inputs else '(geen)'}\n"
        f"Verplichte uitvoer op schijf: {', '.join(outputs) if outputs else '(geen)'}\n"
        "\n"
        "Opdracht:\n"
        f"{brief.get('instruction', '').strip()}\n"
        "\n"
        "Regels:\n"
        "- Roep de genoemde subagent(s) aan. Die staan in .claude/agents/.\n"
        "- Schrijf de genoemde artefacten. Een leeg bestand telt niet.\n"
        "- Voer geen andere fase uit. Start geen volgende stap.\n"
        "- Roep de skill blogpost-workflow niet aan.\n"
        "- Roep scripts/orchestrate.py niet aan. Geen run, complete, approve of reject.\n"
        "- Keur niets goed. Gates zijn niet van jou.\n"
        "- Als je niet kunt afronden: schrijf geen leeg artefact en zeg waarom.\n"
    )


def extract_deploy_ids(text: str) -> tuple[int | None, str | None]:
    """Haal post_id en edit_url uit de uitvoer van de deploy-fase."""
    if not text:
        return None, None
    pid_m = POST_ID_RE.search(text)
    url_m = EDIT_URL_RE.search(text)
    post_id = int(pid_m.group(1)) if pid_m else None
    edit_url = url_m.group(1) if url_m else None
    return post_id, edit_url


def find_running_jobs(
    service: WorkflowService,
    slug: str | None = None,
) -> list[dict[str, Any]]:
    """Posts met status=running, oudste eerst. Alleen die pakt de worker op."""
    root = service.posts_root()
    if not os.path.isdir(root):
        return []

    jobs: list[dict[str, Any]] = []
    names = [slug] if slug else sorted(os.listdir(root))
    for name in names:
        if name.startswith("."):
            continue
        pdir = os.path.join(root, name)
        if not os.path.isdir(pdir) or not os.path.isfile(os.path.join(pdir, "state.json")):
            continue
        try:
            status = service.get_status(post_dir=pdir)
        except (OSError, ValueError, json.JSONDecodeError, KeyError):
            continue
        if status.get("status") != "running":
            continue
        nxt = status.get("next") or {}
        brief = nxt.get("agent_brief")
        if not isinstance(brief, dict):
            continue
        jobs.append(
            {
                "slug": status["slug"],
                "phase": status["phase"],
                "post_dir": status["post_dir"],
                "brief": brief,
                "mtime": os.path.getmtime(os.path.join(pdir, "state.json")),
            }
        )

    jobs.sort(key=lambda j: j["mtime"])
    return jobs


def claude_env(root: str) -> dict[str, str]:
    """Omgeving voor `claude -p`: venv vooraan, zodat agents `python3 scripts/…` vinden."""
    env = os.environ.copy()
    venv_bin = os.path.join(root, ".venv", "bin")
    if os.path.isdir(venv_bin):
        env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
        env["VIRTUAL_ENV"] = os.path.join(root, ".venv")
    return env


def run_claude(
    prompt: str,
    *,
    claude_bin: str,
    timeout_s: int,
    permission_mode: str,
    root: str,
) -> dict[str, Any]:
    """Draai één niet-interactieve Claude Code-sessie. Geen --bare: dat weigert de keychain."""
    cmd = [
        claude_bin,
        "-p",
        prompt,
        "--output-format",
        "json",
        "--permission-mode",
        permission_mode,
        "--no-session-persistence",
        "--disable-slash-commands",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=root,
            env=claude_env(root),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise WorkerError(
            f"claude -p timeout na {timeout_s}s. Fase blijft niet op running; zet blocked."
        ) from exc
    except OSError as exc:
        raise WorkerError(f"claude niet startbaar ({claude_bin}): {exc}") from exc

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    payload: dict[str, Any] = {}
    if stdout.strip():
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = {"result": stdout, "raw": True}

    if proc.returncode != 0 or payload.get("is_error"):
        detail = payload.get("result") or stderr.strip() or stdout.strip() or f"exit {proc.returncode}"
        raise WorkerError(f"claude -p faalde: {detail}")

    return {
        "ok": True,
        "returncode": proc.returncode,
        "result": payload.get("result") or "",
        "payload": payload,
        "stderr": stderr,
    }


def run_once(
    service: WorkflowService,
    *,
    slug: str | None = None,
    dry_run: bool = False,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    claude_bin: str | None = None,
    permission_mode: str = "bypassPermissions",
    runner: Runner | None = None,
    on_claim: OnClaim | None = None,
) -> dict[str, Any]:
    """Pak één running fase, voer de brief uit, roep complete aan. Nooit approve."""
    jobs = find_running_jobs(service, slug=slug)
    if slug and not jobs:
        # Onderscheid: slug bestaat niet, of bestaat maar is niet running.
        try:
            status = service.get_status(post=slug)
        except (FileNotFoundError, ValueError, OSError) as exc:
            return {"ok": False, "action": "idle", "errors": [str(exc)]}
        return {
            "ok": True,
            "action": "idle",
            "slug": slug,
            "phase": status["phase"],
            "status": status["status"],
            "summary": (
                f"{slug} is {status['phase']}/{status['status']}, niet running. "
                "De worker pakt alleen een fase op die al op run staat."
            ),
        }
    if not jobs:
        return {"ok": True, "action": "idle", "summary": "Geen fase met status running."}

    job = jobs[0]
    brief = job["brief"]
    prompt = format_prompt(brief)
    if dry_run:
        return {
            "ok": True,
            "action": "dry_run",
            "slug": job["slug"],
            "phase": job["phase"],
            "prompt": prompt,
            "brief": brief,
        }
    if on_claim is not None:
        on_claim(job)

    execute = runner or (
        lambda p, _job: run_claude(
            p,
            claude_bin=resolve_claude_bin(claude_bin),
            timeout_s=timeout_s,
            permission_mode=permission_mode,
            root=repo_root(),
        )
    )

    try:
        executed = execute(prompt, job)
    except WorkerError as exc:
        blocked = service.mark_blocked(str(exc), post_dir=job["post_dir"])
        return {
            "ok": False,
            "action": "blocked",
            "slug": job["slug"],
            "phase": job["phase"],
            "errors": [str(exc)],
            "status": blocked["status"],
        }

    post_id = None
    edit_url = None
    if job["phase"] == "deploy":
        result_text = ""
        if isinstance(executed, dict):
            result_text = str(executed.get("result") or "")
            inner = executed.get("payload") or {}
            if isinstance(inner, dict) and inner.get("result"):
                result_text = f"{result_text}\n{inner.get('result')}"
        post_id, edit_url = extract_deploy_ids(result_text)

    completed = service.complete_phase(
        phase=job["phase"],
        post_dir=job["post_dir"],
        post_id=post_id,
        edit_url=edit_url,
    )
    if not completed.get("ok"):
        return {
            "ok": False,
            "action": "blocked",
            "slug": job["slug"],
            "phase": job["phase"],
            "errors": completed.get("errors") or ["complete weigerde het artefact"],
            "status": completed.get("status") or "blocked",
        }

    return {
        "ok": True,
        "action": "completed",
        "slug": job["slug"],
        "phase": completed["phase"],
        "status": completed["status"],
        "yolo_advanced": completed.get("yolo_advanced"),
        "gate": completed.get("gate"),
        "next": completed.get("next"),
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Voer één running blogpost-fase uit via Claude Code. Keurt nooit goed."
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--once",
        action="store_true",
        help="Pak één running fase, voer uit, stop (standaard).",
    )
    mode.add_argument(
        "--watch",
        action="store_true",
        help="Herhaal --once tot interrupt. Nog geen productie-daemon.",
    )
    p.add_argument("--post", help="Alleen deze slug, en alleen als die running is.")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Toon de prompt, roep claude niet aan.",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_S,
        help=f"Seconden per fase (standaard {DEFAULT_TIMEOUT_S}).",
    )
    p.add_argument("--claude", help="Pad naar de claude-binary.")
    p.add_argument(
        "--permission-mode",
        default="bypassPermissions",
        choices=(
            "bypassPermissions",
            "acceptEdits",
            "dontAsk",
            "auto",
        ),
        help="Onbeheerd lokaal: bypassPermissions, anders blijft hij op een TTY-prompt hangen.",
    )
    p.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Seconden tussen --watch-pogingen (standaard 30).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = WorkflowService()
    watch = args.watch
    heartbeat = HeartbeatWriter(interval_s=args.interval, timeout_s=args.timeout)
    heartbeat.start()

    def claim(job: dict[str, Any]) -> None:
        heartbeat.update("busy", job)

    # --once is de default als geen van beide is gezet.
    try:
        while True:
            heartbeat.update("idle")
            result = run_once(
                service,
                slug=args.post,
                dry_run=args.dry_run,
                timeout_s=args.timeout,
                claude_bin=args.claude,
                permission_mode=args.permission_mode,
                on_claim=claim,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            heartbeat.update("idle")
            if not watch:
                return 0 if result.get("ok") else 2
            time.sleep(max(1, args.interval))
    finally:
        heartbeat.stop()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
