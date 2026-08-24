#!/usr/bin/env bash
set -e

echo "[*] Starting MHDDoS Web Panel..."

if [ ! -d "node_modules" ]; then
    echo "[!] Dependencies not installed. Please run ./web-install.sh first."
    exit 1
fi

echo "[*] Starting Panel on http://127.0.0.1:5000"
npm start
