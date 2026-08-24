#!/usr/bin/env bash
set -e

echo "[*] MHDDoS Web Panel - Installing dependencies"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[!] python3 could not be found. Please install Python 3."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "[!] npm could not be found. Please install Node.js."
    exit 1
fi

cd ..

echo "[*] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo "[*] Installing Python requirements..."
.venv/bin/python3 -m pip install --upgrade pip --quiet
.venv/bin/python3 -m pip install -r requirements.txt flask

echo "[*] Installing Node.js dependencies..."
cd web
npm install --prefer-offline

echo ""
echo "[+] Installation complete!"
echo "[+] Use ./web-start.sh to launch the panel."
echo ""
