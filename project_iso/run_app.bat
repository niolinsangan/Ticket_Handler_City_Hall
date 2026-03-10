@echo off
setlocal enabledelayedexpansion

cd /d "c:\Users\Niiyyoooww\Desktop\CITY_HALL_ASSIGNMENT\project_dir\Ticket_Handler_City_Hall\project_iso"

echo ========================================
echo City Hall Ticket Handler - Launcher
echo ========================================
echo.

:: Check for Python
echo Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    :: Check if Python exists in common locations
    if exist "c:\Python*\python.exe" (
        set PYTHON_PATH=
        for /d %%i in (c:\Python*) do set PYTHON_PATH=%%i\python.exe
        echo Found Python at: !PYTHON_PATH!
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python*\python.exe" (
        set PYTHON_PATH=
        for /d %%i in ("%LOCALAPPDATA%\Programs\Python\Python*") do set PYTHON_PATH=%%i\python.exe
        echo Found Python at: !PYTHON_PATH!
    ) else if exist "c:\Users\Niiyyoooww\Desktop\CITY_HALL_ASSIGNMENT\cvenv\Scripts\python.exe" (
        set PYTHON_PATH=c:\Users\Niiyyoooww\Desktop\CITY_HALL_ASSIGNMENT\cvenv\Scripts\python.exe
        echo Found Python at: !PYTHON_PATH!
    ) else (
        echo.
        echo [ERROR] Python is not installed or not in PATH!
        echo.
        echo Downloading Python...
        start https://www.python.org/downloads/
        echo Please install Python and run this script again.
        echo.
        pause
        exit /b 1
    )
) else (
    set PYTHON_PATH=python
)

echo Python found: !PYTHON_PATH!
echo.

:: Check for MySQL (optional - not required for SQLite default)
echo Checking for MySQL (optional for SQLite)...
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] MySQL is not installed. This is optional - app uses SQLite by default.
    echo [INFO] If you want MySQL support, you can download it from:
    echo        https://dev.mysql.com/downloads/installer/
    echo.
) else (
    echo MySQL found!
)

echo ========================================
echo Starting City Hall Ticket Handler...
echo ========================================
echo.

:: Open browser to Flask app
start http://localhost:5000
start http://172.20.10.11:5000/

:: Start Flask app in background using pythonw (no terminal window)
start "" "c:\Users\Niiyyoooww\Desktop\CITY_HALL_ASSIGNMENT\cvenv\Scripts\pythonw.exe" app.py

echo App started! Opening browser at http://localhost:5000
echo.
echo To stop the server, close this window and end pythonw.exe in Task Manager.
echo.
exit

