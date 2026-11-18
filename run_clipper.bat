@echo off
setlocal

echo ======================================================================
echo  BEYOND HISTORY - AI LONG VIDEO CLIPPER MODULE
echo ======================================================================
echo.

set "VENV_PY=C:\Users\HP\.faceless-shorts\venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment python not found at:
    echo %VENV_PY%
    pause
    exit /b 1
)

echo Starting AI Long Video Clipper Web Server on http://localhost:8765 ...
start "" http://localhost:8765

"%VENV_PY%" "%~dp0scripts\clipper_server.py" 8765

pause
