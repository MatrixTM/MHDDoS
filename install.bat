@echo off
setlocal

echo [*] MHDDoS - Installing dependencies
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found. Install it from https://python.org and try again.
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Node.js not found. Install it from https://nodejs.org and try again.
    pause
    exit /b 1
)

echo [*] Creating Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
)

echo [*] Installing Python dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt flask
if %errorlevel% neq 0 (
    echo [!] Failed to install Python dependencies.
    pause
    exit /b 1
)

echo [*] Installing Node.js dependencies...
cd web
npm install --prefer-offline
if %errorlevel% neq 0 (
    echo [!] Failed to install Node.js dependencies.
    pause
    exit /b 1
)
cd ..

echo.
echo [+] All dependencies installed successfully.
echo [+] Run start.bat to launch MHDDoS with the web panel.
echo.
pause
