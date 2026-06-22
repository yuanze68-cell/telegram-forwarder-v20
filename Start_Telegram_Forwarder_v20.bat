@echo off
chcp 65001 > nul
echo ================================================
echo   Telegram Forwarder v20 - Smart Album Rewrite
echo ================================================
echo.

REM Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python 3.8+
    pause
    exit /b 1
)

REM Check dependencies
echo [1/3] Checking dependencies...
python -c "import telethon" > nul 2>&1
if errorlevel 1 (
    echo [WARNING] Missing telethon, installing...
    pip install telethon
)

echo [2/3] Starting forwarder v20...
echo.
echo Tips:
echo   - Smart mode: auto-select rewrite method
echo   - Simple mode: forward then send rewritten caption
echo   - Complete mode: not implemented yet (will use simple mode)
echo.
echo ================================================
echo.

REM Start program (use relative path)
python "%~dp0telegram_forwarder_v20.py"

if errorlevel 1 (
    echo.
    echo [ERROR] Program exited abnormally, check error message above
    pause
)

echo.
echo Program exited
pause
