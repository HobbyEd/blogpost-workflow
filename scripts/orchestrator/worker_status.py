"""Heartbeat van de execution-plane worker, te lezen door de control plane.

De worker is een apart proces. FastAPI weet alleen of hij leeft via dit bestand
onder posts/. Een dode pid telt meteen als down; een stil bestand na de
interval ook.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from .repository import now_iso, posts_root

HEARTBEAT_NAME = ".worker_heartbeat.json"
HINT = "Start in een tweede terminal: .venv/bin/python scripts/worker.py --watch"
IDLE_GRACE_S = 15


def heartbeat_path() -> str:
    """Pad naar het heartbeat-bestand, afgeleid van de posts-root."""
    return os.path.join(posts_root(), HEARTBEAT_NAME)


def write_heartbeat(
    *,
    pid: int,
    state: str,
    job: dict[str, Any] | None = None,
    interval_s: int = 30,
    timeout_s: int = 1800,
    started_at: str | None = None,
) -> dict[str, Any]:
    """Schrijf de huidige workerstaat. `started_at` blijft staan bij een refresh van dezelfde job."""
    payload = {
        "pid": pid,
        "state": state,
        "job": job,
        "interval_s": interval_s,
        "timeout_s": timeout_s,
        "updated_at": now_iso(),
        "started_at": started_at if job else None,
    }
    path = heartbeat_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)
    return payload


def clear_heartbeat() -> None:
    """Verwijder het heartbeat-bestand (worker stopt)."""
    path = heartbeat_path()
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def pid_alive(pid: int | None) -> bool:
    """True als het proces nog bestaat. Signaal 0 raakt het proces niet."""
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _age_s(stamp: str | None) -> float | None:
    parsed = _parse_iso(stamp)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed).total_seconds()


def read_status() -> dict[str, Any]:
    """Lees de heartbeat en bepaal of de worker leeft."""
    path = heartbeat_path()
    if not os.path.isfile(path):
        return {
            "alive": False,
            "stale": True,
            "state": "down",
            "pid": None,
            "job": None,
            "updated_at": None,
            "started_at": None,
            "hint": HINT,
        }

    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {
            "alive": False,
            "stale": True,
            "state": "down",
            "pid": None,
            "job": None,
            "updated_at": None,
            "started_at": None,
            "hint": HINT,
        }

    pid = data.get("pid")
    state = data.get("state") or "idle"
    interval_s = int(data.get("interval_s") or 30)
    timeout_s = int(data.get("timeout_s") or 1800)
    age = _age_s(data.get("updated_at"))
    if state == "busy":
        limit = timeout_s
    else:
        limit = max(IDLE_GRACE_S, 2 * interval_s + IDLE_GRACE_S)

    process_gone = not pid_alive(pid)
    file_stale = age is None or age > limit
    stale = process_gone or file_stale
    return {
        "alive": not stale,
        "stale": stale,
        "state": "down" if stale else state,
        "pid": pid,
        "job": data.get("job"),
        "updated_at": data.get("updated_at"),
        "started_at": data.get("started_at"),
        "hint": None if not stale else HINT,
    }
