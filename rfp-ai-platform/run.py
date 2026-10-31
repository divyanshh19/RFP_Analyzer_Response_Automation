"""
One-Command Platform Launcher (Subdirectory redirect)
"""
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TARGET = ROOT_DIR / "run.py"

if TARGET.exists():
    venv_py = ROOT_DIR / "rfp-ai-platform" / "backend" / "venv" / "Scripts" / "python.exe"
    py_exec = str(venv_py) if venv_py.exists() else sys.executable
    sys.exit(subprocess.call([py_exec, str(TARGET)]))
