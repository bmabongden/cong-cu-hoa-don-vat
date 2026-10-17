@echo off
REM Dong goi Cong cu hoa don VAT thanh 1 file EXE (ket qua: dist\CongCuHoaDonVAT.exe)
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :loi
python -m unittest
if errorlevel 1 goto :loi
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name CongCuHoaDonVAT ^
  --icon assets\app.ico ^
  --add-data "assets\app.ico;assets" ^
  main.py
if errorlevel 1 goto :loi
echo.
echo Xong: dist\CongCuHoaDonVAT.exe
exit /b 0
:loi
echo Dong goi that bai.
pause
exit /b 1
