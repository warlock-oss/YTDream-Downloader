# YTDream Downloader — Updated / Perbaikan

## Perubahan pada paket ini

- Pendeteksian FFmpeg/FFprobe menerima path folder maupun path langsung ke executable.
- Pemeriksaan mencari FFmpeg di pengaturan aplikasi, folder `tools/ffmpeg`, `C:\Tools\ffmpeg`, folder ekstraksi `Downloads\ffmpeg*\bin`, dan PATH.
- Jika FFmpeg ditemukan otomatis saat aplikasi dimulai atau Pusat Dependensi dibuka, lokasinya disimpan ke pengaturan agar downloader dapat menggunakannya.
- Perintah versi FFmpeg/FFprobe menggunakan argumen `-version`.
- Pemilihan arsip FFmpeg otomatis tidak lagi mengharuskan nama `win64-gpl-essentials.zip`; nama rilis BtbN yang lazim juga didukung.
- Tombol Periksa Ulang dinonaktifkan selama proses instalasi berjalan untuk mencegah tindakan bertabrakan.
- Disediakan `run.bat`, `setup.bat`, dan `build.bat` di folder utama sebagai pintasan ke skrip dalam `scripts`.

## Hasil pengujian di lingkungan pembuat paket

- Kompilasi sintaks Python (`compileall`): lulus.
- Tes otomatis: 7 lulus.
- Tes runtime Windows dan pembangunan EXE belum dijalankan di lingkungan ini. Harap jalankan `setup.bat`, lalu `run.bat` pada Windows untuk pengujian langsung.

## Catatan maskot

Arsip sumber yang tersedia sebelumnya tidak berisi file gambar maskot asli. Salin gambar Echidna milikmu ke `assets\images\echidna.png` agar tampil di panel kiri. Kode tidak mengganti atau membuat ulang maskot.

## Language support update
- Added a language selector in the main window for Bahasa Indonesia and English.
- The selected language is saved in application settings and restored on next launch.
- Main downloader/settings labels and Dependency Center controls/table headers now switch language.
- Updated quality handling so the English option “Best available” retains the intended best-quality download behavior.
- Validation performed in this environment: `python -m compileall -q src tests` and `pytest -q` (7 passed). GUI interaction and Windows executable packaging still require verification on Windows.
