#!/usr/bin/env bash
# Setup script for Facebook Group Invite Automation
# Usage: bash setup.sh

set -euo pipefail

echo "=== Facebook Group Invite Automation — Setup ==="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 is required but not found."
    echo "Install it from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment…"
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate
echo "Activating virtual environment…"
source venv/bin/activate

# Install dependencies
echo "Installing dependencies…"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Dependencies installed."

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To run the script:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "For help:"
echo "  python main.py --help"
