@echo off
REM ========================================
REM AlphaPilot Pro - Signal Listener Launcher (CMD Version)
REM Alphapilot AI Agent Team
REM Authors: Liang Ziyi, Hou Fengrui, Liang Ruzhen
REM Email: 497720537@qq.com | Phone: 13392077558
REM ========================================

echo.
echo ============================================================
echo   AlphaPilot Pro V9.1 - Signal Listener Launcher (CMD)
echo   Alphapilot AI Agent Team
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "D:\mpython\quant_env\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found, please check the path
    pause
    exit /b 1
)

echo [1/2] Using virtual environment Python...
echo [2/2] Starting signal listener...
echo.

REM Run listener program directly
D:\mpython\quant_env\Scripts\python.exe D:\mpython\listener.py

pause
