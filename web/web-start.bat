@echo off
setlocal

echo [*] Starting MHDDoS Web Panel...

if not exist "node_modules" (
    echo [!] Dependencies not installed. Please run web-install.bat first.
    pause
    exit /b 1
)

echo [*] Starting Panel on http://127.0.0.1:5000
npm start

pause
