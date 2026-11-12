@echo off
title Anti-Forensics & Steganography AI Detection Suite
echo =======================================================================
echo    ANTI-FORENSICS & STEGANOGRAPHY AI DETECTION SUITE
echo    Digital Evidence Screening, Triage & Steganalysis System
echo =======================================================================
echo.
echo [1/2] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b
)

echo [2/2] Starting Forensic Application Server...
echo.
echo Server starting at: http://127.0.0.1:8000
echo Opening web browser...
start http://127.0.0.1:8000
echo.
python app.py
pause

