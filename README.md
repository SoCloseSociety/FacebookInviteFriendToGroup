# Facebook Group Invite Automation

**By [SoClose Society](https://soclose.com)**

Automate the process of inviting your Facebook friends to join a group. The script opens a Chrome browser, lets you log in manually, then automatically selects and invites friends in configurable batches.

---

## Features

- Multi-language support (French & English)
- Configurable batch sizes and invitation limits
- Graceful shutdown with `Ctrl+C`
- Structured logging with timestamps
- Input validation for group URLs
- Automatic ChromeDriver management
- Robust error handling and retry logic

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.8+ |
| Google Chrome | Latest stable |
| pip | Latest |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/SoCloseSociety/FacebookInviteFriendToGroup.git
cd FacebookInviteFriendToGroup
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the script

```bash
python main.py
```

You will be prompted for the Facebook group URL. The browser will open — log in to Facebook, then press **Enter** in the terminal to start the automation.

## Command-Line Options

```
usage: main.py [-h] [--group-url URL] [--lang {fr,en}]
               [--batch-min N] [--batch-max N]
               [--max-invites N] [--headless] [--verbose]

Options:
  --group-url URL      Facebook group URL (prompts if omitted)
  --lang {fr,en}       Facebook UI language (default: fr)
  --batch-min N        Min friends per batch (default: 5)
  --batch-max N        Max friends per batch (default: 10)
  --max-invites N      Stop after N total invites (0 = unlimited)
  --headless           Run Chrome in headless mode
  -v, --verbose        Enable debug logging
```

### Examples

```bash
# French Facebook, default settings
python main.py --group-url "https://www.facebook.com/groups/mygroup"

# English Facebook, batches of 3-7, max 50 invites
python main.py --group-url "https://www.facebook.com/groups/mygroup" \
               --lang en --batch-min 3 --batch-max 7 --max-invites 50

# Verbose mode for debugging
python main.py -v
```

## Project Structure

```
FacebookInviteFriendToGroup/
├── main.py              # Main automation script
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
├── LICENSE              # MIT License
└── README.md            # This file
```

## How It Works

1. **Browser Launch** — Chrome opens via Selenium with notifications disabled.
2. **Manual Login** — You log into Facebook in the browser window.
3. **Group Navigation** — The script navigates to the specified group.
4. **Invite Flow** — It clicks "Invite" → "Invite Facebook friends" to open the dialog.
5. **Friend Selection** — A random batch of friends is selected (checkboxes clicked).
6. **Send** — The "Send invitations" button is clicked.
7. **Repeat** — The process repeats with a delay between batches until all friends are invited or the limit is reached.

## Troubleshooting

| Problem | Solution |
|---|---|
| `ChromeDriver` version mismatch | Update Chrome to latest version, or let `webdriver-manager` handle it automatically |
| Elements not found | Facebook may have updated its UI. Open an issue with details |
| Script stops immediately | Ensure the group URL format is `https://www.facebook.com/groups/...` |
| Permission denied | Make sure you are a member of the group with invite permissions |

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push and open a Pull Request

## Disclaimer

This script is for **educational purposes only**. Automating Facebook interactions may violate Facebook's Terms of Service. Use at your own risk. The authors are not responsible for any consequences resulting from the use of this tool.

## License

[MIT License](LICENSE) — Copyright (c) 2022 Enzo Day

---

*Community project by [SoClose Society](https://soclose.com)*
