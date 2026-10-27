@echo off
setlocal

echo [*] MHDDoS Web Panel - Installing dependencies
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found. Please install Python 3.11 or newer and try again.
    exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [!] Python 3.11 or newer is required.
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Node.js not found. Please install Node.js and try again.
    exit /b 1
)

rem Run from the repository root (this script lives in web\scripts).
cd /d "%~dp0..\.."

echo [*] Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
)

echo [*] Installing Python requirements...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r web\requirements.txt

echo [*] Installing Node.js dependencies...
cd web
npm install --prefer-offline

echo.
echo [+] Installation complete!
echo [+] Start the panel with: python start.py WEB
echo [+] Or run: web\scripts\start.bat
