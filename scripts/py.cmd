@echo off
set "FH=%USERPROFILE%\.faceless-shorts"
if exist "%FH%\venv\Scripts\python.exe" (
    "%FH%\venv\Scripts\python.exe" %*
) else (
    python %*
)
