@echo off
setlocal

echo [*] MHDDoS - Starting web panel

if not exist "web\node_modules" (
    echo [!] Node modules not found. Run install.bat first.
    pause
    exit /b 1
)

echo [*] Starting MHDDoS Panel on http://localhost:5000
start "MHDDoS Panel" cmd /k "cd web && npm start"

timeout /t 2 /nobreak >nul

echo.
echo [+] MHDDoS is running.
echo [+] Open http://localhost:5000 in your browser.
echo [+] Close the terminal window to stop.
echo.
