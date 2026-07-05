@echo off
REM ============================================================
REM  مركز الدليل — تشغيل الموقع محليًا / Run Al-Daleel locally
REM  Double-click this file to start the site.
REM ============================================================
cd /d "%~dp0"
echo.
echo   Starting Al-Daleel Center...
echo   Open your browser at:  http://127.0.0.1:5000
echo   (Press Ctrl+C in this window to stop)
echo.
python app.py
echo.
echo   Server stopped. Press any key to close.
pause >nul
