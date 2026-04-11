@echo off
REM Smart Irrigation System - Quick Setup Script for Windows

echo.
echo ========================================
echo Smart Irrigation System - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Creating .env file template...
if not exist ".env" (
    (
        echo TWILIO_ACCOUNT_SID=ACb52548537ae425e91a38823937901409
        echo TWILIO_AUTH_TOKEN=ccc42b8b4afe47a1ab1a364ff48da3e1
        echo TWILIO_FROM_NUMBER=+17712328309
        echo TWILIO_TO_NUMBER=+919025036336
        echo FLASK_SECRET_KEY=smart_irrigation_secret_key
    ) > .env
    echo Created .env file. Please update with your credentials!
) else (
    echo .env file already exists
)

echo [5/5] Initializing database...
python -c "from app import init_db; init_db(); print('[OK] Database initialized')" 2>nul || (
    echo [INFO] Database will be created on first app run
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application, run:
echo   python app.py
echo.
echo Then open your browser to:
echo   http://localhost:5000
echo.
pause
