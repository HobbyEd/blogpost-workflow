"""Lees Claude-abonnementslimieten en (optioneel) Grok prepaid-saldo.

Claude: dezelfde OAuth-login als Claude Code (`/usage`). Het venster is vijf
uur, niet zes; dat is hoe Anthropic het meet.

Grok: de MCP-server biedt alleen `grok_review`. Het prepaid-saldo zit in de
xAI Management API en vraagt een aparte management-key, niet de inference-key
uit GROK_API_KEY.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

CLAUDE_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CLAUDE_REFRESH_URL = "https://console.anthropic.com/v1/oauth/token"
CLAUDE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
CLAUDE_KEYCHAIN_SERVICE = "Claude Code-credentials"
XAI_API_KEY_URL = "https://api.x.ai/v1/api-key"
XAI_BALANCE_URL = "https://management-api.x.ai/v1/billing/teams/{team_id}/prepaid/balance"

_LOCAL_TZ = ZoneInfo("Europe/Amsterdam")
_CACHE_TTL_S = 45.0
_cache: dict[str, Any] | None = None
_cache_at = 0.0

HttpGet = Callable[[str, dict[str, str]], tuple[int, dict[str, Any] | None, str]]
HttpPost = Callable[[str, dict[str, str], dict[str, Any]], tuple[int, dict[str, Any] | None, str]]


def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def load_env_file(path: str | None = None) -> dict[str, str]:
    """Lees .env zonder python-dotenv. Lege waarden blijven leeg."""
    env: dict[str, str] = {}
    target = path or os.path.join(_repo_root(), ".env")
    if not os.path.isfile(target):
        return env
    with open(target, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            env[key.strip()] = val.strip().strip("'").strip('"')
    return env


def _http_get(url: str, headers: dict[str, str]) -> tuple[int, dict[str, Any] | None, str]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw), raw
            except json.JSONDecodeError:
                return resp.status, None, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw), raw
        except json.JSONDecodeError:
            return exc.code, None, raw
    except Exception as exc:  # noqa: BLE001 — rail mag niet omvallen
        return 0, None, str(exc)


def _http_post(
    url: str, headers: dict[str, str], payload: dict[str, Any]
) -> tuple[int, dict[str, Any] | None, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw), raw
            except json.JSONDecodeError:
                return resp.status, None, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw), raw
        except json.JSONDecodeError:
            return exc.code, None, raw
    except Exception as exc:  # noqa: BLE001
        return 0, None, str(exc)


def _env_key(env: dict[str, str], *names: str) -> str | None:
    for name in names:
        val = (env.get(name) or os.environ.get(name) or "").strip()
        if val:
            return val
    return None


def read_claude_credentials() -> dict[str, Any] | None:
    """Lees de Claude Code-login uit de macOS-sleutelhanger."""
    try:
        out = subprocess.check_output(
            ["security", "find-generic-password", "-s", CLAUDE_KEYCHAIN_SERVICE, "-w"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    try:
        data = json.loads(out.strip())
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def write_claude_credentials(payload: dict[str, Any], account: str | None = None) -> bool:
    """Schrijf een ververste OAuth-set terug. Alleen aanroepen na een geslaagde refresh."""
    acct = account or os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    if not acct:
        return False
    try:
        subprocess.run(
            [
                "security",
                "add-generic-password",
                "-U",
                "-a",
                acct,
                "-s",
                CLAUDE_KEYCHAIN_SERVICE,
                "-w",
                json.dumps(payload),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def _oauth_blob(creds: dict[str, Any]) -> dict[str, Any]:
    blob = creds.get("claudeAiOauth")
    return blob if isinstance(blob, dict) else {}


def _token_expired(blob: dict[str, Any], skew_s: int = 60) -> bool:
    raw = blob.get("expiresAt")
    if raw is None:
        return False
    try:
        expires = int(raw)
    except (TypeError, ValueError):
        return False
    if expires > 10_000_000_000:
        expires = expires / 1000.0
    return time.time() >= (expires - skew_s)


def refresh_claude_oauth(
    creds: dict[str, Any],
    http_post: HttpPost = _http_post,
) -> dict[str, Any] | None:
    """Vernieuw het access-token. Schrijft alleen terug bij succes."""
    blob = _oauth_blob(creds)
    refresh = blob.get("refreshToken") or blob.get("refresh_token")
    if not refresh:
        return None
    status, body, _ = http_post(
        CLAUDE_REFRESH_URL,
        {"Content-Type": "application/json"},
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": CLAUDE_CLIENT_ID,
        },
    )
    if status != 200 or not isinstance(body, dict):
        return None
    access = body.get("access_token") or body.get("accessToken")
    if not access:
        return None
    new_refresh = body.get("refresh_token") or body.get("refreshToken") or refresh
    expires_in = body.get("expires_in") or body.get("expiresIn") or 3600
    try:
        expires_at = int(time.time() + int(expires_in)) * 1000
    except (TypeError, ValueError):
        expires_at = int((time.time() + 3600) * 1000)
    blob = dict(blob)
    blob["accessToken"] = access
    blob["refreshToken"] = new_refresh
    blob["expiresAt"] = expires_at
    updated = dict(creds)
    updated["claudeAiOauth"] = blob
    write_claude_credentials(updated)
    return updated


def _window(raw: dict[str, Any] | None, label: str) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    used = raw.get("utilization")
    if used is None:
        used = raw.get("used_percentage")
    try:
        used_pct = float(used)
    except (TypeError, ValueError):
        return None
    used_pct = max(0.0, min(100.0, used_pct))
    resets = raw.get("resets_at")
    return {
        "label": label,
        "used_pct": used_pct,
        "available_pct": round(100.0 - used_pct, 1),
        "resets_at": resets,
        "resets_at_local": _format_local(resets),
    }


def _format_local(value: Any) -> str | None:
    if not value:
        return None
    text = str(value)
    try:
        if text.isdigit():
            dt = datetime.fromtimestamp(int(text), tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt.astimezone(_LOCAL_TZ)
    except (TypeError, ValueError, OSError):
        return text
    return local.strftime("%a %d %b %H:%M").replace(".", "")


def fetch_claude_usage(
    http_get: HttpGet = _http_get,
    http_post: HttpPost = _http_post,
    creds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Haal 5-uur- en weeklimiet op. Zonder login: ok=False, geen exception."""
    stored = creds if creds is not None else read_claude_credentials()
    if not stored:
        return {
            "ok": False,
            "error": "Geen Claude Code-login gevonden in de sleutelhanger.",
        }
    blob = _oauth_blob(stored)
    if _token_expired(blob):
        refreshed = refresh_claude_oauth(stored, http_post=http_post)
        if refreshed:
            stored = refreshed
            blob = _oauth_blob(stored)
    token = blob.get("accessToken") or blob.get("access_token")
    if not token:
        return {"ok": False, "error": "Claude-login heeft geen access-token."}

    headers = {
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        "Content-Type": "application/json",
    }
    status, body, _ = http_get(CLAUDE_USAGE_URL, headers)
    if status == 401:
        refreshed = refresh_claude_oauth(stored, http_post=http_post)
        if refreshed:
            blob = _oauth_blob(refreshed)
            token = blob.get("accessToken") or blob.get("access_token")
            headers["Authorization"] = f"Bearer {token}"
            status, body, _ = http_get(CLAUDE_USAGE_URL, headers)
    if status != 200 or not isinstance(body, dict):
        return {
            "ok": False,
            "error": f"Claude usage-API gaf HTTP {status}.",
        }
    return {
        "ok": True,
        "subscription": blob.get("subscriptionType"),
        "tier": blob.get("rateLimitTier"),
        "session": _window(body.get("five_hour"), "5-uur venster"),
        "week": _window(body.get("seven_day"), "weekbudget"),
        "error": None,
    }


def fetch_grok_credits(
    env: dict[str, str] | None = None,
    http_get: HttpGet = _http_get,
) -> dict[str, Any]:
    """Prepaid-saldo via de xAI Management API. Inference-key is niet genoeg."""
    merged = load_env_file()
    if env:
        merged.update(env)
    inference = _env_key(merged, "GROK_API_KEY", "XAI_API_KEY")
    management = _env_key(merged, "XAI_MANAGEMENT_KEY", "XAI_MANAGEMENT_API_KEY")
    hint = (
        "Maak een management key aan op console.x.ai → Settings → Management Keys "
        "en zet die in .env als XAI_MANAGEMENT_KEY. De Grok-MCP-server heeft "
        "alleen grok_review; credits zitten niet op die tool."
    )
    team_id = None
    if inference:
        status, info, _ = http_get(
            XAI_API_KEY_URL,
            {"Authorization": f"Bearer {inference}", "Content-Type": "application/json"},
        )
        if status == 200 and isinstance(info, dict):
            team_id = info.get("team_id")
    if not management:
        return {
            "ok": False,
            "remaining_usd": None,
            "team_id": team_id,
            "error": "Geen xAI-managementkey. Inference-key mag billing niet lezen.",
            "hint": hint,
        }
    if not team_id:
        return {
            "ok": False,
            "remaining_usd": None,
            "team_id": None,
            "error": "Geen team_id: GROK_API_KEY ontbreekt of /v1/api-key faalde.",
            "hint": hint,
        }
    status, body, raw = http_get(
        XAI_BALANCE_URL.format(team_id=team_id),
        {"Authorization": f"Bearer {management}", "Content-Type": "application/json"},
    )
    if status != 200 or not isinstance(body, dict):
        return {
            "ok": False,
            "remaining_usd": None,
            "team_id": team_id,
            "error": f"xAI billing gaf HTTP {status}.",
            "hint": hint if status in {0, 401, 403} else raw[:240],
        }
    total = body.get("total")
    cents = total.get("val") if isinstance(total, dict) else total
    try:
        remaining = abs(int(cents)) / 100.0
    except (TypeError, ValueError):
        return {
            "ok": False,
            "remaining_usd": None,
            "team_id": team_id,
            "error": "Billingantwoord had geen leesbaar saldo.",
            "hint": None,
        }
    return {
        "ok": True,
        "remaining_usd": remaining,
        "team_id": team_id,
        "error": None,
        "hint": None,
    }


def collect_usage(
    *,
    use_cache: bool = True,
    http_get: HttpGet = _http_get,
    http_post: HttpPost = _http_post,
    env: dict[str, str] | None = None,
    claude_creds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bundel Claude-limieten en Grok-saldo voor de UI."""
    global _cache, _cache_at
    now = time.time()
    if use_cache and _cache is not None and (now - _cache_at) < _CACHE_TTL_S:
        return _cache
    payload = {
        "ok": True,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "claude": fetch_claude_usage(
            http_get=http_get, http_post=http_post, creds=claude_creds
        ),
        "grok": fetch_grok_credits(env=env, http_get=http_get),
    }
    if use_cache:
        _cache = payload
        _cache_at = now
    return payload
