"""Start the W3 FastAPI backend with the isolated virtual environment.

Usage:
    C:/Users/wzd/.workbuddy/binaries/python/envs/tea-backend/Scripts/python.exe scripts/start_backend.py

The isolated venv already contains FastAPI + ML dependencies, so no
PYTHONPATH hack is required. Run this script from PowerShell or cmd on Windows.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = Path(sys.executable)

env = os.environ.copy()
env["TEA_JWT_SECRET"] = env.get("TEA_JWT_SECRET", "dev-secret-change-me-in-production")

cmd = [
    str(PYTHON),
    "-m",
    "uvicorn",
    "src.backend.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--reload",
]

print("Starting backend...")
print("Project root:", PROJECT_ROOT)
print("Command:", " ".join(cmd))
subprocess.run(cmd, cwd=PROJECT_ROOT, env=env)
