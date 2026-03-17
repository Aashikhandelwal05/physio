@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting Physio Prescription Manager...
echo Open your browser and go to: http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.

python run.py
pause