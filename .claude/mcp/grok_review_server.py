#!/usr/bin/env python3
"""Grok-review MCP-server.

Een minimale MCP-server (stdio, JSON-RPC 2.0, newline-gescheiden) die één tool
biedt: grok_review(text, focus). De tool stuurt een blogpost-concept naar de
xAI-API (OpenAI-compatibel) met een vaste kritische persona als system prompt, en
geeft de ruwe kritiek terug.

Geen externe dependencies; alleen de Python-standaardlibrary. De API-key komt uit
het .env-bestand in de projectroot en staat nooit in de code of de repo.
"""

import json
import os
import sys
import urllib.request
import urllib.error

XAI_URL = "https://api.x.ai/v1/chat/completions"
DEFAULT_MODEL = "grok-4.3"
HERE = os.path.dirname(os.path.abspath(__file__))


def find_up(filename):
    """Zoek een bestand omhoog vanaf deze scriptmap tot de schijfwortel."""
    d = HERE
    while True:
        candidate = os.path.join(d, filename)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def load_dotenv():
    """Lees .env uit de projectroot. Tolerant voor 'sleutel = \"waarde\"'."""
    env = {}
    path = find_up(".env")
    if not path:
        return env
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip().lower().replace("-", "_")
            val = val.strip().strip("'").strip('"').strip()
            env[key] = val
    return env


_ENV = load_dotenv()


def get_api_key():
    for name in ("api_key", "xai_api_key", "grok_api_key"):
        if _ENV.get(name):
            return _ENV[name]
    # laatste redmiddel: echte omgevingsvariabele
    return os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY")


def get_model():
    return _ENV.get("grok_model") or os.environ.get("GROK_MODEL") or DEFAULT_MODEL


def load_persona():
    path = os.path.join(HERE, "grok-reviewer-persona.md")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ("Je bent een scherpe, ervaren criticus van vakinhoudelijke "
                "blogposts. Geef concrete, genummerde kritiek in het Nederlands.")


def call_grok(text, focus=""):
    """Stuur de tekst naar Grok met de kritische persona; geef de kritiek terug."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Geen API-key gevonden in .env (verwacht 'GROK_API_KEY = ...' of 'XAI_API_KEY = ...')."
        )

    user_content = text
    if focus:
        user_content = f"Focus van deze review: {focus}\n\n---\n\n{text}"

    payload = {
        "model": get_model(),
        "messages": [
            {"role": "system", "content": load_persona()},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.4,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        XAI_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"xAI HTTP {exc.code}: {detail}") from exc
    return body["choices"][0]["message"]["content"]


# ------------------------- MCP-protocol (stdio) -------------------------

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "grok-review", "version": "0.1.0"}

TOOL_DEF = {
    "name": "grok_review",
    "description": (
        "Stuur een blogpost-concept naar Grok (xAI) voor scherpe, inhoudelijke "
        "kritiek met een vaste kritische persona. Geeft de ruwe kritiek terug als "
        "tekst. Gebruik dit in de kritiekfase van de blogpost-workflow."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "De volledige concepttekst (markdown) om te laten reviewen.",
            },
            "focus": {
                "type": "string",
                "description": "Optioneel: waar de review zich vooral op moet richten.",
            },
        },
        "required": ["text"],
    },
}

CREDITS_TOOL_DEF = {
    "name": "grok_credits",
    "description": (
        "Geef het resterende xAI prepaid-saldo terug. Vereist XAI_MANAGEMENT_KEY; "
        "GROK_API_KEY alleen is niet genoeg. Gebruik dit niet voor een review."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


def _call_grok_credits(req_id):
    """Lees prepaid-saldo. Zelfde bron als GET /api/usage in de web-UI."""
    repo = find_up(".env")
    root = os.path.dirname(repo) if repo else os.path.abspath(os.path.join(HERE, "..", ".."))
    scripts = os.path.join(root, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        from orchestrator.provider_usage import fetch_grok_credits
        info = fetch_grok_credits()
    except Exception as exc:  # noqa: BLE001
        return make_result(req_id, {
            "content": [{"type": "text", "text": f"Fout bij grok_credits: {exc}"}],
            "isError": True,
        })
    if info.get("ok"):
        tekst = f"Resterend prepaid-saldo: ${info['remaining_usd']:.2f}."
    else:
        tekst = info.get("error") or "Saldo niet beschikbaar."
        if info.get("hint"):
            tekst = f"{tekst} {info['hint']}"
    return make_result(req_id, {
        "content": [{"type": "text", "text": tekst}],
        "isError": not info.get("ok"),
    })


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def make_result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(msg):
    method = msg.get("method")
    req_id = msg.get("id")
    is_notification = "id" not in msg

    if method == "initialize":
        return make_result(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })

    if method in ("notifications/initialized", "initialized"):
        return None  # notificatie, geen antwoord

    if method == "ping":
        return make_result(req_id, {})

    if method == "tools/list":
        return make_result(req_id, {"tools": [TOOL_DEF, CREDITS_TOOL_DEF]})

    if method == "tools/call":
        params = msg.get("params", {}) or {}
        name = params.get("name")
        if name == "grok_credits":
            return _call_grok_credits(req_id)
        if name != "grok_review":
            return make_error(req_id, -32601, f"Onbekende tool: {name}")
        args = params.get("arguments", {}) or {}
        text = args.get("text", "")
        focus = args.get("focus", "")
        if not text.strip():
            return make_result(req_id, {
                "content": [{"type": "text", "text": "Fout: 'text' is leeg."}],
                "isError": True,
            })
        try:
            critique = call_grok(text, focus)
            return make_result(req_id, {
                "content": [{"type": "text", "text": critique}],
            })
        except Exception as exc:  # noqa: BLE001 - fout terug naar de client
            return make_result(req_id, {
                "content": [{"type": "text", "text": f"Fout bij grok_review: {exc}"}],
                "isError": True,
            })

    if is_notification:
        return None
    return make_error(req_id, -32601, f"Onbekende methode: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(msg)
        if response is not None:
            send(response)


if __name__ == "__main__":
    main()
