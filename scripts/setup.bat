@echo off
setlocal
cd /d "%~dp0\.."
echo [YTDream] Menyiapkan lingkungan virtual...
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher tidak ditemukan. Pasang Python 3.12 dari python.org, lalu jalankan ulang.
  exit /b 1
)
py -3.12 --version >nul 2>nul
if errorlevel 1 (
  echo Python 3.12 tidak ditemukan. Proyek ini menargetkan Python 3.10-3.13; Python 3.15 belum ditargetkan karena kompatibilitas paket GUI perlu dipastikan.
  echo Pasang Python 3.12 berdampingan. Instalasi Python yang sudah ada tidak akan dihapus.
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.12 -m venv .venv
if not exist ".venv\Scripts\python.exe" (echo GAGAL membuat .venv. & exit /b 1)
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -e ".[dev]"
if errorlevel 1 (echo Instalasi dependensi gagal. Periksa koneksi dan keluaran terminal. & exit /b 1)
echo Selesai. Jalankan scripts\run.bat
