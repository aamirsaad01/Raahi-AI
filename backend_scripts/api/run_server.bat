@echo off
REM Quick start script for Windows
echo ============================================================
echo  Raahi AI Backend API Server - Starting...
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist "..\venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run: pip install -r ..\requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call ..\venv\Scripts\activate.bat

REM Check if .env exists
if not exist "..\..\..\.env" (
    echo [WARNING] .env file not found in project root!
    echo Please create .env file with database credentials
    echo.
)

REM Start server
python app.py

pause

