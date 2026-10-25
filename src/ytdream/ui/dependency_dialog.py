from __future__ import annotations
import logging, sys
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTableWidget,QTableWidgetItem,QProgressBar,QMessageBox,QPlainTextEdit
from ..services.dependency_checker import check_dependencies, find_ffmpeg_directory
from ..services.dependency_installer import install_python_package, install_ffmpeg, DependencyInstallError

class InstallWorker(QObject):
    progress=Signal(int,str); done=Signal(str); failed=Signal(str)
    def __init__(self, action): super().__init__(); self.action=action
    def run(self):
        try: self.progress.emit(10,"Menyiapkan proses…"); result=self.action(); self.progress.emit(100,"Verifikasi selesai"); self.done.emit(str(result or "Instalasi berhasil"))
        except Exception as e: self.failed.emit(str(e))

class DependencyDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent); self.config=config; self.setWindowTitle("Pusat Dependensi — YTDream Downloader"); self.resize(850,520); self._thread=None; self._worker=None
        layout=QVBoxLayout(self); self.intro=QLabel(); layout.addWidget(self.intro)
        self.table=QTableWidget(0,4); self.table.setHorizontalHeaderLabels(["Komponen","Dibutuhkan","Terdeteksi","Status"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); layout.addWidget(self.table)
        self.progress=QProgressBar(); self.progress.setValue(0); layout.addWidget(self.progress); self.stage=QLabel(); layout.addWidget(self.stage)
        row=QHBoxLayout(); self.check_btn=QPushButton("Periksa Semua"); self.install_btn=QPushButton("Pasang Semua yang Diperlukan"); self.ffmpeg_btn=QPushButton("Pasang FFmpeg"); self.recheck_btn=QPushButton("Periksa Ulang"); self.log_btn=QPushButton("Buka log teknis"); close_btn=QPushButton("Tutup")
        self.close_btn=close_btn
        for b in (self.check_btn,self.install_btn,self.ffmpeg_btn,self.recheck_btn,self.log_btn,close_btn): row.addWidget(b)
        layout.addLayout(row); self.check_btn.clicked.connect(self.refresh); self.recheck_btn.clicked.connect(self.refresh); self.install_btn.clicked.connect(self.install_required); self.ffmpeg_btn.clicked.connect(self.install_ffmpeg); self.log_btn.clicked.connect(self.show_logs); close_btn.clicked.connect(self.accept); self.apply_language(); self.refresh()
    def apply_language(self):
        en = self.config.data.get("language", "id") == "en"
        self.setWindowTitle("Dependency Center — YTDream Downloader" if en else "Pusat Dependensi — YTDream Downloader")
        self.intro.setText("Check components, versions, and application requirements. Python packages may only be installed inside a virtual environment." if en else "Periksa komponen, versi, dan kebutuhan aplikasi. Instalasi paket Python hanya diizinkan dalam virtual environment.")
        self.table.setHorizontalHeaderLabels(["Component", "Required", "Detected", "Status"] if en else ["Komponen", "Dibutuhkan", "Terdeteksi", "Status"])
        self.check_btn.setText("Check All" if en else "Periksa Semua")
        self.install_btn.setText("Install Required Components" if en else "Pasang Semua yang Diperlukan")
        self.ffmpeg_btn.setText("Install FFmpeg" if en else "Pasang FFmpeg")
        self.recheck_btn.setText("Recheck" if en else "Periksa Ulang")
        self.log_btn.setText("Open technical log" if en else "Buka log teknis")
        self.close_btn.setText("Close" if en else "Tutup")
        if not self.stage.text() or self.stage.text() in ("Pemeriksaan belum dilakukan.", "Check has not been run yet."):
            self.stage.setText("Check has not been run yet." if en else "Pemeriksaan belum dilakukan.")

    def refresh(self):
        configured = self.config.data.get("ffmpeg_path", "")
        if not configured:
            detected_dir = find_ffmpeg_directory()
            if detected_dir:
                self.config.data["ffmpeg_path"] = detected_dir
                self.config.save()
                configured = detected_dir
        statuses=check_dependencies(bundled=bool(getattr(sys,"frozen",False)), ffmpeg_path=configured); self.table.setRowCount(len(statuses))
        for r,s in enumerate(statuses):
            for c,v in enumerate((s.name,s.required,s.detected,s.status)):
                display = v
                if self.config.data.get("language", "id") == "en":
                    translations = {"Belum tersedia":"Not installed", "Tersedia":"Available", "Siap":"Ready", "Siap digunakan":"Ready to use", "Sudah dibundel":"Bundled", "Versi tidak kompatibel":"Incompatible version", "Periksa resource":"Check resources", "Perlu perhatian":"Needs attention", "Wajib":"Required", "Opsional":"Optional", "Tidak diketahui":"Unknown", "Versi kompatibel":"Compatible version", "Versi sesuai requirements.txt":"Version per requirements.txt", "Maskot dan konfigurasi":"Mascot and configuration"}
                    display = translations.get(v, v)
                    if c == 0:
                        display = {"Python runtime":"Python runtime", "Resource aplikasi":"Application resources"}.get(display, display)
                item=QTableWidgetItem(display); item.setToolTip(s.detail); self.table.setItem(r,c,item)
        self.table.resizeColumnsToContents(); self.stage.setText((f"Check complete: {len(statuses)} components checked." if self.config.data.get("language")=="en" else f"Pemeriksaan selesai: {len(statuses)} komponen diperiksa.")); self.progress.setValue(100)
    def _start(self, action, label):
        if self._thread and self._thread.isRunning(): return
        self.check_btn.setEnabled(False); self.install_btn.setEnabled(False); self.ffmpeg_btn.setEnabled(False); self.recheck_btn.setEnabled(False); self.progress.setValue(0); self.stage.setText(label)
        self._thread=QThread(self); self._worker=InstallWorker(action); self._worker.moveToThread(self._thread); self._thread.started.connect(self._worker.run); self._worker.progress.connect(self._on_progress); self._worker.done.connect(self._on_done); self._worker.failed.connect(self._on_failed); self._worker.done.connect(self._thread.quit); self._worker.failed.connect(self._thread.quit); self._thread.finished.connect(self._restore); self._thread.start()
    def _on_progress(self,value,message): self.progress.setValue(value); self.stage.setText(message)
    def _on_done(self,message): self.stage.setText(message); self.refresh(); QMessageBox.information(self,"Process complete" if self.config.data.get("language")=="en" else "Proses selesai",message)
    def _on_failed(self,message): logging.error("Dependency installation failed: %s",message); self.stage.setText("Process failed; details were written to the log." if self.config.data.get("language")=="en" else "Proses gagal; detail dicatat di log."); QMessageBox.warning(self,"Installation failed" if self.config.data.get("language")=="en" else "Instalasi gagal",message)
    def _restore(self): self.check_btn.setEnabled(True); self.install_btn.setEnabled(True); self.ffmpeg_btn.setEnabled(True); self.recheck_btn.setEnabled(True); self._worker=None; self._thread=None
    def install_required(self):
        statuses=check_dependencies(bundled=bool(getattr(sys,"frozen",False)),ffmpeg_path=self.config.data.get("ffmpeg_path","")); missing=[s.name for s in statuses if s.status=="Belum tersedia" and s.name in ("yt-dlp","PySide6")]
        if not missing: QMessageBox.information(self,"Tidak perlu instalasi","Tidak ada paket Python wajib yang terdeteksi hilang. Periksa status FFmpeg secara terpisah jika diperlukan."); return
        if not (sys.prefix != getattr(sys,"base_prefix",sys.prefix) or getattr(sys,"frozen",False)):
            QMessageBox.warning(self,"Virtual environment diperlukan","Demi keamanan, paket tidak dipasang ke Python global. Jalankan setup.bat untuk menyiapkan .venv lalu buka aplikasi dari run.bat."); return
        if QMessageBox.question(self,"Konfirmasi instalasi","Paket yang hilang akan dipasang ke lingkungan aplikasi. Lanjutkan?") != QMessageBox.StandardButton.Yes: return
        def action():
            for package in ("PySide6>=6.7,<7", "yt-dlp[default]>=2025.1.0"):
                name=package.split("[",1)[0].split(">",1)[0]
                if name in missing: install_python_package(package)
            return "Instalasi paket selesai; lakukan Periksa Ulang untuk verifikasi."
        self._start(action,"Memasang paket Python yang diperlukan…")
    def install_ffmpeg(self):
        if QMessageBox.question(self,"Konfirmasi FFmpeg","Unduh arsip FFmpeg dari rilis GitHub BtbN dan ekstrak ffmpeg.exe/ffprobe.exe ke folder tools aplikasi?\n\nCatatan: rilis tidak selalu menyediakan checksum resmi; unduhan menggunakan HTTPS tetapi integritas kriptografis tidak dapat dijamin jika checksum tidak tersedia.") != QMessageBox.StandardButton.Yes: return
        def action():
            path=install_ffmpeg(); self.config.data["ffmpeg_path"]=str(path); self.config.save(); return f"FFmpeg diekstrak ke {path}. Periksa ulang untuk verifikasi."
        self._start(action,"Mengunduh dan mengekstrak FFmpeg…")
    def show_logs(self):
        from ..utils.paths import log_dir
        p=log_dir()/"ytdream.log"; dlg=QDialog(self); dlg.setWindowTitle("Log teknis"); dlg.resize(760,420); lay=QVBoxLayout(dlg); box=QPlainTextEdit(); box.setReadOnly(True)
        try: box.setPlainText(p.read_text(encoding="utf-8",errors="replace"))
        except OSError: box.setPlainText("Belum ada log.")
        lay.addWidget(box); dlg.exec()
