@echo off
REM ============================================================
REM  مركز الدليل — تشغيل الموقع محليًا / Run Al-Daleel locally
REM  Double-click this file. It installs what's needed, then runs.
REM ============================================================
cd /d "%~dp0"
echo.
echo   ============================================
echo    Al-Daleel Center  -  Setup ^& Run
echo   ============================================
echo.
echo   Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo   [!] Python is not installed or not in PATH.
  echo       Install it from:  https://www.python.org/downloads/
  echo       ^(During install, tick "Add Python to PATH"^)
  echo.
  pause
  exit /b
)

echo   Installing required packages ^(first run may take a minute^)...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo   [!] Could not install the required packages.
  echo       Check your internet connection and try again.
  echo.
  pause
  exit /b
)

echo.
echo   Starting the site (LOCAL development mode)...
echo   Open your browser at:  http://127.0.0.1:5000
echo   (Press Ctrl+C in this window to stop)
echo   To put this online for the public, see DEPLOY.md
echo.
REM Local dev only: enable auto-reload/debug. Never used in production.
set FLASK_DEBUG=1
python app.py
echo.
echo   Server stopped. Press any key to close.
pause >nul
