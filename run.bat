@echo off
setlocal

echo [*] MHDDoS - Starting web panel

if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)

if not exist "web\node_modules" (
    echo [!] Node modules not found. Run install.bat first.
    pause
    exit /b 1
)

echo [*] Starting Flask API server on http://localhost:5000
start "MHDDoS - Flask API" cmd /k ".venv\Scripts\python.exe web\app.py"

timeout /t 2 /nobreak >nul

echo [*] Starting web panel on http://localhost:3000
start "MHDDoS - Web Panel" cmd /k "cd web && npm start"

echo.
echo [+] MHDDoS is running.
echo [+] Open http://localhost:3000 in your browser.
echo [+] Close the terminal windows to stop.
echo.
