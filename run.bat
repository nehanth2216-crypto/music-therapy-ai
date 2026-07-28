@echo off
echo ===================================================
echo Starting HarmonyRec AI Music Therapy Application...
echo ===================================================
echo.

:: Start FastAPI Backend Server in a new window
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "HarmonyRec Backend (FastAPI)" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

:: Pause briefly to allow backend to initialize
timeout /t 3 /nobreak >nul

:: Start React + Vite Frontend Server in a new window
echo [2/2] Starting React + Vite Frontend on http://localhost:5173 ...
start "HarmonyRec Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo Application started successfully!
echo.
echo Backend API Docs: http://127.0.0.1:8000/docs
echo Frontend App:    http://localhost:5173
echo ===================================================
