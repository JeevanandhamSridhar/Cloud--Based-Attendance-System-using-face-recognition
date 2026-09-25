@echo off
title Smart Attendance Launcher
echo ======================================================================
echo    SMART ATTENDANCE SYSTEM - FACIAL RECOGNITION & ATTENFACE ANALYTICS
echo ======================================================================
echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Smart Attendance Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe run_server.py"

echo [2/2] Launching React Vite Frontend on http://localhost:5173 ...
start "Smart Attendance Frontend" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

echo.
echo ======================================================================
echo  System is running!
echo  - Frontend Dashboard: http://localhost:5173
echo  - Interactive Swagger API: http://127.0.0.1:8000/docs
echo ======================================================================
pause
