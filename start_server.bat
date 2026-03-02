@echo off
REM Start the Flask development server on Windows

echo Starting SP Backend Server...
echo.

REM Check if venv exists, if not create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Start the server
echo.
echo ========================================
echo Starting Flask server on localhost:5000
echo ========================================
echo.
echo API will be available at: http://localhost:5000
echo API documentation: See README.md
echo.
echo To stop the server, press Ctrl+C
echo.

python app.py

pause
