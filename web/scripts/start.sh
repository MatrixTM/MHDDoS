#!/usr/bin/env bash
set -e

# Run from the web directory (this script lives in web/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[*] Starting MHDDoS Web Panel..."

if [ ! -d "node_modules" ]; then
    echo "[!] Dependencies not installed. Please run bash web/scripts/install.sh first."
    exit 1
fi

echo "[*] Starting Panel on http://127.0.0.1:5000"
if [ -d "../.venv/bin" ]; then
    export PATH="$PWD/../.venv/bin:$PATH"
fi
npm start
