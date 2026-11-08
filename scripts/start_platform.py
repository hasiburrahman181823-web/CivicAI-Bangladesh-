"""
CivicAI Bangladesh - Cross-Platform Dual-Process Launcher
Starts both FastAPI backend (port 8000) and Vite frontend (port 5173).
"""

import os
import sys
import subprocess
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 65)
    print(">> Launching CivicAI Bangladesh Full-Stack Platform")
    print("=" * 65)

    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    frontend_cmd = ["npm", "run", "dev"]

    print("[1/2] Starting Backend API Server (http://localhost:8000)...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=base_dir)

    time.sleep(2)

    print("[2/2] Starting Frontend SPA Server (http://localhost:5173)...")
    frontend_dir = os.path.join(base_dir, "frontend")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=frontend_dir, shell=True)

    print("\n-------------------------------------------------------------")
    print("🚀 CivicAI Bangladesh is LIVE!")
    print("👉 Frontend Application: http://localhost:5173")
    print("👉 Interactive API Docs:  http://localhost:8000/api/docs")
    print("👉 Health Check Endpoint: http://localhost:8000/api/health")
    print("-------------------------------------------------------------")
    print("Press Ctrl+C to terminate both servers.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping platform servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
