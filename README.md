# Blogpost-workflow

Deterministische control plane in Python, agents voor het schrijven, gates bij
de auteur. Live publiceren blijft handwerk in wp-admin.

**Nieuwe sessie (Grok, Claude Code, Antigravity):** lees `AGENTS.md`.

| Wat je zoekt | Waar |
|---|---|
| Architectuur | `adr/` |
| Huisstijl / deploy | `reference/huisstijl.md`, `reference/deploy.md` |
| Keten + terminal | `opzet_blogpost_workflow.html` |
| Overige documenten | `docs/README.md` |

## Lokaal starten

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env_template .env   # keys invullen
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn server:app --reload --port 8000
.venv/bin/python scripts/worker.py --watch
```

De worker voert fases met `status: running` uit via Claude Code. Hij keurt
nooit een gate goed.

## Secrets

`.env` (gitignored): `GROK_API_KEY`, `WP_*`, `ADMIN_TOKEN`, `GEMINI_API_KEY`.
Sjabloon: `.env_template`.
