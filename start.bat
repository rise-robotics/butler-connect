@echo off
title Butler Connect - Unitree Go2 Controller

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                    🤖 Butler Connect                      ║
echo ║               Unitree Go2 Robot Controller                ║
echo ║                                                          ║
echo ║                   Windows Launcher                       ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo 💡 Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is available
echo.

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo ❌ requirements.txt not found
    echo 💡 Please run this script from the butler-connect project directory
    pause
    exit /b 1
)

echo 📁 Project directory confirmed
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment found
)

echo.
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 🔧 Installing/updating dependencies...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo 💡 Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ✅ Dependencies installed successfully
echo.

REM Create logs directory
if not exist "logs" mkdir logs

REM Check configuration files
echo 🔍 Checking configuration files...
if exist "config\robot_config.yaml" (
    echo ✅ robot_config.yaml
) else (
    echo ❌ robot_config.yaml missing
)

if exist "config\control_config.yaml" (
    echo ✅ control_config.yaml
) else (
    echo ❌ control_config.yaml missing
)

if exist "config\safety_config.yaml" (
    echo ✅ safety_config.yaml
) else (
    echo ❌ safety_config.yaml missing
)

echo.
echo 🚀 Starting Butler Connect...
echo 📱 Web interface: http://localhost:8000
echo 📖 API docs: http://localhost:8000/docs
echo.
echo ⚠️  SAFETY REMINDER:
echo    - Keep emergency stop ready
echo    - Ensure robot has space to move
echo    - Check battery level
echo.
echo 🛑 Press Ctrl+C to stop
echo ════════════════════════════════════════════════════════════
echo.

REM Start the application
python src\main.py

echo.
echo 🛑 Butler Connect stopped
echo ✅ Thank you for using Butler Connect!
pause
