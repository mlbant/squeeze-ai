@echo off
REM Squeeze AI Deployment Script for Windows
REM This script helps deploy the Squeeze AI application on Windows

echo 🚀 Squeeze AI Deployment Script (Windows)
echo ==========================================

REM Check if .env file exists
if not exist ".env" (
    echo ❌ Error: .env file not found!
    echo Please create .env file with your production credentials.
    echo See PRODUCTION_SETUP.md for details.
    pause
    exit /b 1
)

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.9+ and try again
    pause
    exit /b 1
)

echo ✅ Python installation check passed

:menu
echo.
echo Please select deployment option:
echo 1. Install dependencies
echo 2. Initialize database
echo 3. Test local setup
echo 4. Run application locally
echo 5. Generate secure credentials
echo 6. Full setup (1+2+3)
echo 0. Exit
echo.

set /p choice="Enter your choice [0-6]: "

if "%choice%"=="1" goto install_deps
if "%choice%"=="2" goto init_db
if "%choice%"=="3" goto test_setup
if "%choice%"=="4" goto run_app
if "%choice%"=="5" goto gen_creds
if "%choice%"=="6" goto full_setup
if "%choice%"=="0" goto exit
echo ❌ Invalid option. Please try again.
goto menu

:install_deps
echo 📦 Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    goto menu
)
echo ✅ Dependencies installed successfully
goto menu

:init_db
echo 🗄️ Initializing database...
python database.py
if errorlevel 1 (
    echo ❌ Failed to initialize database
    pause
    goto menu
)
echo ✅ Database initialized successfully
goto menu

:test_setup
echo 🧪 Testing local setup...
python -c "import streamlit; print('✅ Streamlit import successful')"
if errorlevel 1 (
    echo ❌ Streamlit not properly installed
    pause
    goto menu
)

python -c "import sqlite3; conn = sqlite3.connect('squeeze_ai.db'); conn.close(); print('✅ Database connection test passed')"
if errorlevel 1 (
    echo ❌ Database connection failed
    pause
    goto menu
)

echo ✅ Local setup test passed
goto menu

:run_app
echo 🚀 Starting Squeeze AI application...
echo 🌐 Application will be available at http://localhost:8501
echo Press Ctrl+C to stop the application
streamlit run app.py
goto menu

:gen_creds
echo 🔐 Generating secure credentials...
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
echo.
echo Copy the SECRET_KEY above and update your .env file
pause
goto menu

:full_setup
echo 🚀 Starting full setup...
call :install_deps
call :init_db
call :test_setup
echo 🎉 Full setup completed!
echo You can now run the application with option 4
goto menu

:exit
echo 👋 Goodbye!
pause
exit /b 0
