@echo off
REM WhatsApp Chat Analyzer - Quick Setup for Windows
echo =========================================
echo   WhatsApp Chat Analyzer - Quick Setup
echo =========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [INFO] Python detected successfully

REM Install dependencies
echo [INFO] Installing dependencies from requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [SUCCESS] Dependencies installed successfully

REM Check for stop_hinglish.txt
if not exist stop_hinglish.txt (
    echo [WARNING] stop_hinglish.txt not found - creating default...
    copy nul stop_hinglish.txt
    echo the >> stop_hinglish.txt
    echo a >> stop_hinglish.txt
    echo an >> stop_hinglish.txt
    echo and >> stop_hinglish.txt
    echo or >> stop_hinglish.txt
    echo but >> stop_hinglish.txt
    echo in >> stop_hinglish.txt
    echo on >> stop_hinglish.txt
    echo at >> stop_hinglish.txt
    echo to >> stop_hinglish.txt
    echo for >> stop_hinglish.txt
    echo of >> stop_hinglish.txt
    echo with >> stop_hinglish.txt
    echo by >> stop_hinglish.txt
    echo from >> stop_hinglish.txt
    echo up >> stop_hinglish.txt
    echo about >> stop_hinglish.txt
    echo into >> stop_hinglish.txt
    echo through >> stop_hinglish.txt
    echo during >> stop_hinglish.txt
    echo before >> stop_hinglish.txt
    echo after >> stop_hinglish.txt
    echo is >> stop_hinglish.txt
    echo are >> stop_hinglish.txt
    echo was >> stop_hinglish.txt
    echo were >> stop_hinglish.txt
    echo be >> stop_hinglish.txt
    echo been >> stop_hinglish.txt
    echo being >> stop_hinglish.txt
    echo have >> stop_hinglish.txt
    echo has >> stop_hinglish.txt
    echo had >> stop_hinglish.txt
    echo do >> stop_hinglish.txt
    echo does >> stop_hinglish.txt
    echo did >> stop_hinglish.txt
    echo will >> stop_hinglish.txt
    echo would >> stop_hinglish.txt
    echo shall >> stop_hinglish.txt
    echo should >> stop_hinglish.txt
    echo may >> stop_hinglish.txt
    echo might >> stop_hinglish.txt
    echo must >> stop_hinglish.txt
    echo can >> stop_hinglish.txt
    echo could >> stop_hinglish.txt
    echo i >> stop_hinglish.txt
    echo you >> stop_hinglish.txt
    echo he >> stop_hinglish.txt
    echo she >> stop_hinglish.txt
    echo it >> stop_hinglish.txt
    echo we >> stop_hinglish.txt
    echo they >> stop_hinglish.txt
    echo them >> stop_hinglish.txt
    echo their >> stop_hinglish.txt
    echo your >> stop_hinglish.txt
    echo my >> stop_hinglish.txt
    echo his >> stop_hinglish.txt
    echo her >> stop_hinglish.txt
    echo its >> stop_hinglish.txt
    echo this >> stop_hinglish.txt
    echo that >> stop_hinglish.txt
    echo these >> stop_hinglish.txt
    echo those >> stop_hinglish.txt
    echo ka >> stop_hinglish.txt
    echo ki >> stop_hinglish.txt
    echo ke >> stop_hinglish.txt
    echo ko >> stop_hinglish.txt
    echo se >> stop_hinglish.txt
    echo mein >> stop_hinglish.txt
    echo par >> stop_hinglish.txt
    echo aur >> stop_hinglish.txt
    echo hai >> stop_hinglish.txt
    echo hain >> stop_hinglish.txt
    echo tha >> stop_hinglish.txt
    echo the >> stop_hinglish.txt
    echo thi >> stop_hinglish.txt
    echo raha >> stop_hinglish.txt
    echo rahe >> stop_hinglish.txt
    echo rahi >> stop_hinglish.txt
    echo kar >> stop_hinglish.txt
    echo karke >> stop_hinglish.txt
    echo karna >> stop_hinglish.txt
    echo hoga >> stop_hinglish.txt
    echo hoge >> stop_hinglish.txt
    echo hogi >> stop_hinglish.txt
    echo sakta >> stop_hinglish.txt
    echo sakte >> stop_hinglish.txt
    echo sakti >> stop_hinglish.txt
    echo chahiye >> stop_hinglish.txt
    echo apna >> stop_hinglish.txt
    echo tum >> stop_hinglish.txt
    echo aap >> stop_hinglish.txt
    echo main >> stop_hinglish.txt
    echo hum >> stop_hinglish.txt
    echo yeh >> stop_hinglish.txt
    echo woh >> stop_hinglish.txt
    echo kya >> stop_hinglish.txt
    echo kyun >> stop_hinglish.txt
    echo kaise >> stop_hinglish.txt
    echo kahan >> stop_hinglish.txt
    echo kab >> stop_hinglish.txt
    echo kitna >> stop_hinglish.txt
    echo kitne >> stop_hinglish.txt
    echo itna >> stop_hinglish.txt
    echo utna >> stop_hinglish.txt
    echo jab >> stop_hinglish.txt
    echo tab >> stop_hinglish.txt
    echo jahan >> stop_hinglish.txt
    echo tahan >> stop_hinglish.txt
    echo jaisa >> stop_hinglish.txt
    echo aisa >> stop_hinglish.txt
    echo waisa >> stop_hinglish.txt
    echo maam >> stop_hinglish.txt
    echo ma'am >> stop_hinglish.txt
    echo sir >> stop_hinglish.txt
    echo miss >> stop_hinglish.txt
    echo mrs >> stop_hinglish.txt
    echo mr >> stop_hinglish.txt
    echo dr >> stop_hinglish.txt
    echo prof >> stop_hinglish.txt
    echo hello >> stop_hinglish.txt
    echo hi >> stop_hinglish.txt
    echo hey >> stop_hinglish.txt
    echo ok >> stop_hinglish.txt
    echo okay >> stop_hinglish.txt
    echo thanks >> stop_hinglish.txt
    echo thank >> stop_hinglish.txt
    echo please >> stop_hinglish.txt
)

echo [SUCCESS] File check completed

REM Create necessary directories
if not exist exports mkdir exports
if not exist .cache mkdir .cache

echo [SUCCESS] Directories created

echo.
echo =========================================
echo   Setup Complete! 
echo =========================================
echo.
echo To run the application:
echo   streamlit run Chat_Analysiser_app.py
echo.
echo Or double-click this file again and select option 2
echo.
echo 1. Run WhatsApp Chat Analyzer now
echo 2. Exit
echo.

set /p choice="Enter your choice (1 or 2): "
if "%choice%"=="1" (
    echo [INFO] Starting WhatsApp Chat Analyzer...
    streamlit run Chat_Analysiser_app.py
) else (
    echo [INFO] Setup complete. Exiting...
    pause
)
