@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (echo Lingkungan belum disiapkan. Jalankan scripts\setup.bat terlebih dahulu. & pause & exit /b 1)
set PYTHONPATH=%CD%\src
.venv\Scripts\python.exe -m ytdream.main
if errorlevel 1 pause
