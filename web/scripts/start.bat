@echo off
setlocal

echo [*] Starting MHDDoS Web Panel...

rem Run from the web directory (this script lives in web\scripts).
cd /d "%~dp0.."

if not exist "node_modules" (
    echo [!] Dependencies not installed. Please run web\scripts\install.bat first.
    exit /b 1
)

echo [*] Starting Panel on http://127.0.0.1:5000
set "PATH=%CD%\..\.venv\Scripts;%PATH%"
npm start
