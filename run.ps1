# PowerShell launcher for Autonomous RFP Analyzer
Set-Location -Path $PSScriptRoot

$VenvPython = Join-Path $PSScriptRoot "rfp-ai-platform\backend\venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython "run.py"
} else {
    python "run.py"
}
