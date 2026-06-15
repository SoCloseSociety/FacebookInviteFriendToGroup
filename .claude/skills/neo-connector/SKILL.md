---
name: neo-connector
description: Audit this repo's connectivity surface for NeoBot and regenerate NEO_CONNECTOR.md. Use when asked to wire this project to Neo, refresh the connector manifest, or check whether it exposes an API.
---

# Neo Connector audit -- fbinvitegroup

Goal: keep `NEO_CONNECTOR.md` an accurate, code-proven manifest of how (or whether)
NeoBot can talk to this repo. Never invent endpoints; prove everything from source.
Uncertain -> put it under `## Gaps`.

## Current verdict
NOT WIREABLE as an HTTP connector. This is a pure local CLI (Selenium browser
automation) in a single `main.py`. No HTTP/REST/WS/webhook server, no served port,
no `.env`. Its only interface is the argparse CLI, and it requires an interactive
manual Facebook login, so it cannot run unattended.

## How to re-audit
1. Inventory source: `find . -name '*.py' -not -path './.git/*'`.
2. Look for any server: `grep -rniE 'flask|fastapi|aiohttp|uvicorn|django|bottle|http.server|web\.Application|@app\.(route|get|post)|listen\(|run_polling|webhook' . --include='*.py'`.
3. If still no server -> verdict stays NOT WIREABLE; document the CLI in `NEO_CONNECTOR.md` (args from `parse_args` in `main.py`).
4. If a server is ever added -> document base_url, auth, and every endpoint (method, path, auth, input, output, errors, curl example), mirroring the SuiteForge `editsforge/NEO_CONNECTOR.md` format.
5. Do NOT modify source code during an audit. Only write `NEO_CONNECTOR.md`, this skill, the CLAUDE.md "Neo Connector (auto)" section, and the pre-commit hook.

## Files this audit owns
- `NEO_CONNECTOR.md` (the manifest)
- `CLAUDE.md` -> "## Neo Connector (auto)"
- `.claude/skills/neo-connector/SKILL.md` (this file)
- `.git/hooks/pre-commit` (staleness warning)
