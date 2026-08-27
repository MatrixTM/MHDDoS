@echo off
setlocal

echo [*] MHDDoS Web Panel - Installing dependencies
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python not found. Please install Python 3 and try again.
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Node.js not found. Please install Node.js and try again.
    pause
    exit /b 1
)

cd ..

echo [*] Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
)

echo [*] Installing Python requirements...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt flask

echo [*] Installing Node.js dependencies...
cd web
npm install --prefer-offline

echo.
echo [+] Installation complete!
echo [+] Use web-start.bat to launch the panel.
echo.
pause
