@echo off
TITLE Autonomous RFP Analyzer & Response Automation Platform
cd /d "%~dp0"

IF EXIST "rfp-ai-platform\backend\venv\Scripts\python.exe" (
    "rfp-ai-platform\backend\venv\Scripts\python.exe" run.py
) ELSE (
    python run.py
)

pause
