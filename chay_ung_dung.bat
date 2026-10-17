@echo off
REM Chay Cong cu hoa don VAT tu ma nguon (lan dau se tu cai PySide6 neu chua co)
cd /d "%~dp0"
where python >nul 2>nul || (echo Chua tim thay Python. Hay cai Python 3.10 tro len tu python.org va tick "Add python.exe to PATH". & pause & exit /b 1)
python -c "import PySide6" 2>nul || python -m pip install -r requirements.txt
python main.py
if errorlevel 1 pause
