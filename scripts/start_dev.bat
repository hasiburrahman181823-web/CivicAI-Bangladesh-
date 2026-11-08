@echo off
echo ========================================================
echo Starting CivicAI Bangladesh Full-Stack Platform...
echo ========================================================

echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "CivicAI Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting React Vite Frontend on http://localhost:5173 ...
start "CivicAI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both services are launching in separate windows:
echo - Backend API & Docs: http://localhost:8000/api/docs
echo - Frontend Web App:   http://localhost:5173
echo ========================================================
pause
