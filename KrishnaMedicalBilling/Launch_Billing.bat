@echo off
echo Starting Krishna Medical Billing System...
echo Please wait while we load the system...

:: Check if python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found! Please install Python to run this software.
    pause
    exit
)

:: Install dependencies if needed (quietly)
echo Checking system requirements...
pip install flask pandas >nul 2>&1

:: Start the Server
echo Stopping old server instances...
taskkill /IM python.exe /F >nul 2>&1

echo Launching Application...
start "" "http://127.0.0.1:5000"
python app.py

pause
