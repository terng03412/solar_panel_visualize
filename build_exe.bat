@echo off
echo Building the Flask app into an executable...
pip install pyinstaller
pyinstaller --onefile --add-data "C:\Users\terng\Downloads\devon\solar_eval\templates;templates" app.py
echo Build complete. Check the 'dist' directory for the executable.
pause
