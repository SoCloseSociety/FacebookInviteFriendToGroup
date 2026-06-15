# CLAUDE.md -- FacebookInviteFriendToGroup

## 1. Project Identity

**Name:** FacebookInviteFriendToGroup -- Facebook Group Invite Automation
**Role:** Automate inviting Facebook friends to groups with batch processing, multi-language support (FR/EN), and configurable batch sizes.
**Author:** SoClose Society (https://soclose.co)
**License:** MIT

### Stack

- **Language:** Python 3.9+
- **Browser:** Selenium 4.x with webdriver-manager
- **Parsing:** BeautifulSoup4
- **Architecture:** Monolithic (single main.py, 496 LOC)

### Critical Files

- `main.py` -- All logic (496 LOC)
- No config files, no .env -- CLI args only

## 2-5. Standard Workflow

- Enter plan mode for non-trivial tasks
- Test with `--max-invites 5` first
- Verify batch processing and delay logic work
- Track tasks in `tasks/todo.md`, lessons in `tasks/lessons.md`

## 6. Project-Specific Rules

### Dev Commands
```bash
pip install -r requirements.txt
python main.py --group-url "https://facebook.com/groups/..." --lang fr
python main.py --group-url "..." --batch-size 3 7 --max-invites 20
python main.py --headless --group-url "..."
```

### CLI Arguments
- --group-url URL -- Facebook group URL (required)
- --lang fr|en -- Language (default: fr)
- --batch-size MIN MAX -- Batch range (default: 5 10)
- --max-invites N -- Max invitations (default: 0=unlimited)
- --headless -- Headless browser

### Known Fragile Areas
- Facebook DOM changes frequently -- XPath selectors break
- Multi-language selectors (FR/EN) -- button text varies by locale
- Manual login required -- Facebook detects automated login aggressively
- Batch invite dialog -- parsing "N FRIENDS SELECTED" text is fragile

## 7. Core Principles

- Simplicity First, No Laziness, Minimal Impact
- Never use em dashes (use -- instead)

## Neo Connector (auto)

- Slug: `fbinvitegroup`
- Verdict: NOT WIREABLE -- pure local CLI (Selenium browser automation), no HTTP server.
- Manifest: `NEO_CONNECTOR.md` (proven from `main.py`; regenerate via the Neo Connector audit).
- Interface: `python main.py --group-url ... [--lang fr|en] [--batch-min N] [--batch-max N] [--max-invites N] [--headless]`. Requires Chrome + a manual Facebook login (interactive `input()` prompt), so it cannot run unattended.
- For Neo: there is nothing to call over the network. Do not invent endpoints. If wiring is ever needed, a separate HTTP job-runner wrapper would have to be built (out of scope; would modify the project).
- When `main.py` / `requirements.txt` change, re-run the audit and regenerate `NEO_CONNECTOR.md`. The pre-commit hook warns if `main.py` changed without touching `NEO_CONNECTOR.md`.
