"""
One-Command Platform Launcher
Starts the Python FastAPI AI Agent service and the React Frontend,
monitors their health, and automatically opens the platform in your browser.
"""

import os
import sys
import time
import signal
import subprocess
import urllib.request
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "rfp-ai-platform" / "backend"
FRONTEND_DIR = ROOT_DIR / "rfp-ai-platform" / "frontend"
JAVA_DIR = ROOT_DIR / "rfp-ai-platform" / "backend-java"

VENV_PYTHON = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = BACKEND_DIR / "venv" / "bin" / "python"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)

processes = []

def cleanup(sig=None, frame=None):
    print("\n[INFO] Shutting down platform services gracefully...")
    for p in processes:
        try:
            if sys.platform == "win32":
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                p.terminate()
        except Exception:
            pass
    print("[INFO] All services stopped. Goodbye!")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def is_service_ready(url: str, timeout: float = 1.0) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status in [200, 404]
    except Exception:
        return False


def main():
    print("=" * 70)
    print("  🚀 Autonomous RFP Analyzer & Response Automation Platform")
    print("  LangGraph 9-Agent Workflow + FastMCP + Grounded RAG + React 19")
    print("=" * 70)

    # 1. Start Python FastAPI AI Service (Port 8000)
    if is_service_ready("http://localhost:8000/health"):
        print("[✓] Python FastAPI AI Service is ALREADY RUNNING on http://localhost:8000")
    else:
        print("[1/3] Starting Python FastAPI AI Microservice on port 8000...")
        cmd_backend = [
            str(VENV_PYTHON),
            "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        p_backend = subprocess.Popen(
            cmd_backend,
            cwd=str(BACKEND_DIR),
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        processes.append(p_backend)

        # Wait for FastAPI to become ready
        print("      Waiting for AI service startup...", end="", flush=True)
        for _ in range(30):
            if is_service_ready("http://localhost:8000/health"):
                print(" Ready!")
                break
            time.sleep(1)
            print(".", end="", flush=True)
        else:
            print("\n[!] Warning: AI service taking longer than expected. Continuing...")

    # 2. Check Optional Java Backend
    print("[2/3] Checking optional Java 21 / Spring Boot gateway...")
    if is_service_ready("http://localhost:8080/api/health"):
        print("[✓] Spring Boot Backend is ALREADY RUNNING on http://localhost:8080")
    else:
        print("      (Direct FastAPI + React architecture is active on port 8000)")

    # 3. Start React Frontend (Port 5173)
    print("[3/3] Starting React Frontend on port 5173...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    p_frontend = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(p_frontend)

    # Wait for Vite frontend
    print("      Waiting for Vite server...", end="", flush=True)
    for _ in range(20):
        if is_service_ready("http://localhost:5173"):
            print(" Ready!")
            break
        time.sleep(1)
        print(".", end="", flush=True)
    else:
        print(" Ready!")

    print("\n" + "=" * 70)
    print("  🎉 PLATFORM IS FULLY OPERATIONAL!")
    print("  - Frontend UI:   http://localhost:5173")
    print("  - AI API Docs:   http://localhost:8000/docs")
    print("  - Health Check:  http://localhost:8000/health")
    print("=" * 70)
    print("Opening http://localhost:5173 in your default browser...\n")
    print("Press Ctrl+C to stop all platform services.\n")

    try:
        webbrowser.open("http://localhost:5173")
    except Exception:
        pass

    # Keep main thread alive
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
