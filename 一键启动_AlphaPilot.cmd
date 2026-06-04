@echo off
REM ========================================
REM AlphaPilot Pro - One-Click Dual Window Launcher (CMD Version)
REM Alphapilot AI Agent Team
REM Authors: Liang Ziyi, Hou Fengrui, Liang Ruzhen
REM Email: 497720537@qq.com | Phone: 13392077558
REM ========================================

echo.
echo ============================================================
echo   AlphaPilot Pro V9.1 - Quick Start System
echo   Alphapilot AI Agent Team
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "D:\mpython\quant_env\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found, please check the path
    pause
    exit /b 1
)

echo [1/3] Checking environment... OK
echo [2/3] Starting main strategy engine (new window)...
echo [3/3] Starting signal listener (new window)...
echo.
echo ============================================================
echo   Two independent windows opened. Keep them both running!
echo   Close window = Stop corresponding program
echo ============================================================
echo.

REM Start first window: Main Strategy
start "AlphaPilot - Main Strategy Engine" cmd /k "cd /d D:\mpython && echo. && echo ======================================== && echo   AlphaPilot Pro V9.1 - Main Strategy Engine && echo ======================================== && echo. && D:\mpython\quant_env\Scripts\python.exe D:\mpython\main.py"

REM Wait 1 second to avoid window overlap
timeout /t 1 /nobreak >nul

REM Start second window: Signal Listener
start "AlphaPilot - Signal Listener" cmd /k "cd /d D:\mpython && echo. && echo ======================================== && echo   AlphaPilot Pro V9.1 - Signal Listener && echo ======================================== && echo. && D:\mpython\quant_env\Scripts\python.exe D:\mpython\listener.py"

echo.
echo SUCCESS: Both windows started successfully!
echo.
echo TIPS:
echo    - Left window: Main Strategy Engine (Trade Execution)
echo    - Right window: Signal Listener (File Monitor)
echo    - Keep both windows running simultaneously
echo    - Closing any window will stop its function
echo.
pause
