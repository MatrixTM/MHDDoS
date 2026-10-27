#!/usr/bin/env bash
set -e

# Run from the repository root (this script lives in web/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "[*] MHDDoS Web Panel - Installing dependencies"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[!] python3 could not be found. Please install Python 3.11 or newer."
    exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "[!] Python 3.11 or newer is required."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "[!] npm could not be found. Please install Node.js."
    exit 1
fi

echo "[*] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo "[*] Installing Python requirements..."
.venv/bin/python3 -m pip install --upgrade pip --quiet
.venv/bin/python3 -m pip install -r web/requirements.txt

echo "[*] Installing Node.js dependencies..."
cd web
npm install --prefer-offline

echo ""
echo "[+] Installation complete!"
echo "[+] Start the panel with: python start.py WEB"
echo "[+] Or run: bash web/scripts/start.sh"
