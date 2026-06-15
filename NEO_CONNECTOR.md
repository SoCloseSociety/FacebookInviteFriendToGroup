# NEO_CONNECTOR -- fbinvitegroup
- service: fbinvitegroup
- base_url_prod: none (no HTTP server)
- auth: none (no network surface; Facebook session is a manual browser login)
- env_required: []
- generated_at:

> Machine-readable connection manifest for NeoBot. Everything below is proven from
> code. Do NOT edit by hand -- regenerate via the Neo Connector audit.
>
> VERDICT: NOT WIREABLE as an HTTP connector. This repo is a pure local CLI tool
> (Selenium browser automation), not a service. There is no HTTP/REST/WS/webhook
> surface for Neo to call. It can only be invoked as a subprocess on a host that
> has Chrome + an interactive Facebook login.

## What this is (proven from `main.py`)
- Entry point: `main.py` -> `main()` (single file, no other `*.py` in repo).
- Type: argparse CLI that drives Chrome via Selenium (`webdriver.Chrome`) +
  BeautifulSoup DOM parsing to invite Facebook friends to a group in batches.
- Deps (`requirements.txt`): `selenium`, `beautifulsoup4`, `webdriver-manager`.
  No web framework (no flask/fastapi/aiohttp/uvicorn/django/bottle/http.server).
- Networking: only outbound, via the controlled Chrome browser hitting
  `https://www.facebook.com/`. The script opens no socket and serves no port.

## Invocation (the only "interface")
```bash
pip install -r requirements.txt
python main.py --group-url "https://facebook.com/groups/<GROUP>" --lang fr \
  --batch-min 5 --batch-max 10 --max-invites 20 [--headless] [--verbose]
```
- CLI args (from `parse_args`): `--group-url` (str; prompts interactively if omitted),
  `--lang {fr,en}` (default `fr`), `--batch-min` (int, default 5),
  `--batch-max` (int, default 10), `--max-invites` (int, default 0 = unlimited),
  `--headless` (flag), `--verbose`/`-v` (flag).
- Runtime requires a human: it opens Facebook and waits on
  `input("...press Enter to start")` after a manual login. Not automatable headless
  end-to-end (login step). Graceful stop on SIGINT/SIGTERM (finishes current batch).
- Output: logs to stdout only (`logging`, format `%(asctime)s [%(levelname)s] %(message)s`).
  No machine-readable result, no exit-code contract beyond `sys.exit(1)` on invalid URL.

## Endpoints
None. No HTTP server exists in this repo.

## Gaps
- No HTTP/REST/GraphQL/WebSocket/webhook server anywhere in the codebase (verified:
  grep for flask/fastapi/aiohttp/uvicorn/django/bottle/http.server/web.Application/
  listen/@app.route returned nothing).
- No `.env`, no config file (CLAUDE.md confirms "CLI args only"); no API keys/tokens.
- To make this Neo-callable you would have to wrap it (e.g. a small HTTP job-runner
  that shells out to `main.py` and reports status). That wrapper does not exist today
  and writing it would modify/extend the project -- out of scope for this audit.
- The manual-login + interactive-prompt design means even a subprocess wrapper cannot
  run it unattended without code changes to the login flow.
