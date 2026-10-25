@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\pyinstaller.exe" (echo PyInstaller belum tersedia. Jalankan scripts\setup.bat terlebih dahulu. & exit /b 1)
if not exist "launcher.py" (echo launcher.py tidak ditemukan. Pastikan folder proyek lengkap. & exit /b 1)
.venv\Scripts\pyinstaller.exe --noconfirm --clean --windowed --name YTDream-Downloader --onedir --paths src --add-data "assets;assets" launcher.py
if errorlevel 1 exit /b 1
echo Build selesai: dist\YTDream-Downloader\YTDream-Downloader.exe
echo Uji executable pada Windows sebelum distribusi.
