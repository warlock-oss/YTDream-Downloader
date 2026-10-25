from __future__ import annotations
import logging
from pathlib import Path
from PySide6.QtCore import Qt,QThread
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QFrame,QSplitter,QLineEdit,QPushButton,QComboBox,QCheckBox,QProgressBar,QListWidget,QListWidgetItem,QFileDialog,QMessageBox,QTabWidget,QFormLayout,QSpinBox,QSizePolicy)
from ..core.config import AppConfig
from ..services.downloader import DownloadWorker,validate_url
from ..services.dependency_checker import find_ffmpeg_directory
from ..services.queue_manager import QueueManager,QueueTask
from ..utils.paths import resource_path
from .dependency_dialog import DependencyDialog

STYLE="""QMainWindow,QWidget{background:#151315;color:#eee9e9;font-family:'Segoe UI';font-size:10pt} QFrame#panel{background:#201b1e;border:1px solid #56303c;border-radius:12px} QLabel#brand{font-size:18pt;font-weight:700;color:#f5eeee} QLabel#credit{color:#c99aa7} QPushButton{background:#632638;color:#fff;border:1px solid #8c4057;border-radius:7px;padding:8px 12px} QPushButton:hover{background:#80334b} QPushButton:disabled{background:#393438;color:#8c8588} QLineEdit,QComboBox,QSpinBox,QListWidget{background:#100f11;border:1px solid #57434a;border-radius:6px;padding:7px;color:#f3eeee} QProgressBar{border:1px solid #57434a;border-radius:5px;text-align:center;background:#100f11} QProgressBar::chunk{background:#8b304b;border-radius:4px} QTabWidget::pane{border:1px solid #57434a} QTabBar::tab{background:#282226;padding:8px 14px} QTabBar::tab:selected{background:#632638} QSplitter::handle{background:#56303c} QCheckBox{spacing:8px}"""
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("YTDream Downloader — Echidna Edition"); self.resize(1180,760); self.setMinimumSize(900,620); self.setStyleSheet(STYLE); self.config=AppConfig(); self.queue=QueueManager(); self.active_thread=None; self.active_worker=None
        if not self.config.data.get("ffmpeg_path"):
            detected_ffmpeg = find_ffmpeg_directory()
            if detected_ffmpeg:
                self.config.data["ffmpeg_path"] = detected_ffmpeg
                self.config.save()
        central=QWidget(); root=QVBoxLayout(central); root.setContentsMargins(18,14,18,18); root.setSpacing(14); self.setCentralWidget(central)
        header=QHBoxLayout(); brand=QLabel("YTDream Downloader"); brand.setObjectName("brand"); edition=QLabel("ECHIDNA EDITION"); edition.setStyleSheet("color:#bd8797;letter-spacing:2px"); header.addWidget(brand); header.addWidget(edition); header.addStretch(); credit=QLabel("MADE BY  warlock-oss"); credit.setObjectName("credit"); header.addWidget(credit); self.language_combo=QComboBox(); self.language_combo.addItem("Bahasa Indonesia", "id"); self.language_combo.addItem("English", "en"); self.language_combo.setCurrentIndex(1 if self.config.data.get("language")=="en" else 0); header.addWidget(self.language_combo); root.addLayout(header)
        splitter=QSplitter(Qt.Orientation.Horizontal); splitter.setChildrenCollapsible(False); root.addWidget(splitter,1)
        self.mascot_panel=QFrame(); self.mascot_panel.setObjectName("panel"); ml=QVBoxLayout(self.mascot_panel); ml.setContentsMargins(10,10,10,10); self.mascot=QLabel(); self.mascot.setAlignment(Qt.AlignmentFlag.AlignCenter); self.mascot.setMinimumSize(0,0); self.mascot.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored); ml.addWidget(self.mascot,1); self._mascot_pixmap=None; self.mascot_hint=QLabel("ECHIDNA • ORIGINAL ASSET"); self.mascot_hint.setAlignment(Qt.AlignmentFlag.AlignCenter); self.mascot_hint.setStyleSheet("color:#bd8797;letter-spacing:2px"); ml.addWidget(self.mascot_hint); splitter.addWidget(self.mascot_panel)
        self.feature_panel=QFrame(); self.feature_panel.setObjectName("panel"); fr=QVBoxLayout(self.feature_panel); fr.setContentsMargins(14,14,14,14); self.tabs=QTabWidget(); fr.addWidget(self.tabs); splitter.addWidget(self.feature_panel); splitter.setSizes([560,560]); splitter.setStretchFactor(0,1); splitter.setStretchFactor(1,1)
        self._load_mascot(); self._build_download_tab(); self._build_settings_tab(); self._sync_queue(); self.language_combo.currentIndexChanged.connect(self._language_changed); self._apply_language()
    def _load_mascot(self):
        p=resource_path("assets","images","echidna.png")
        if p.exists():
            pix=QPixmap(str(p))
            if not pix.isNull():
                self._mascot_pixmap=pix
                self.mascot_hint.hide()
                self._fit_mascot()
            else:
                self._show_mascot_placeholder("File echidna.png tidak dapat dibaca.")
        else:
            self._show_mascot_placeholder("Maskot belum tersedia\n\nLetakkan gambar asli di:\nassets/images/echidna.png")

    def _show_mascot_placeholder(self, message):
        self.mascot.setText("ECHIDNA\n\n" + message)
        self.mascot.setStyleSheet("color:#bd8797;font-size:11pt;border:1px dashed #8c4057;border-radius:12px")

    def _fit_mascot(self):
        """Scale the original mascot to the current label area without cropping or distortion."""
        if self._mascot_pixmap is None or self._mascot_pixmap.isNull():
            return
        available=self.mascot.contentsRect().size()
        if available.width() < 1 or available.height() < 1:
            return
        self.mascot.setPixmap(self._mascot_pixmap.scaled(
            available,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_mascot()
    def _build_download_tab(self):
        tab=QWidget(); outer=QVBoxLayout(tab); form=QFormLayout(); self.url=QLineEdit(); self.url.setPlaceholderText("Tempel URL video atau playlist…"); self.url_label=QLabel("URL media"); form.addRow(self.url_label,self.url); self.kind=QComboBox(); self.kind.addItems(["Video","Audio MP3"]); self.kind_label=QLabel("Jenis"); form.addRow(self.kind_label,self.kind); self.format=QComboBox(); self.format.addItems(["MP4","MKV"]); self.format_label=QLabel("Format video"); form.addRow(self.format_label,self.format); self.quality=QComboBox(); self.quality.addItems(["Terbaik tersedia","2160p","1440p","1080p","720p","480p","360p"]); self.quality_label=QLabel("Kualitas maksimum"); form.addRow(self.quality_label,self.quality); outer.addLayout(form)
        options=QHBoxLayout(); self.playlist=QCheckBox("Playlist"); self.subtitles=QCheckBox("Unduh subtitle"); self.auto_subs=QCheckBox("Subtitle otomatis"); options.addWidget(self.playlist); options.addWidget(self.subtitles); options.addWidget(self.auto_subs); outer.addLayout(options)
        outrow=QHBoxLayout(); self.output=QLineEdit(self.config.data.get("output_dir",str(Path.home()/"Downloads"))); browse=QPushButton("Pilih folder"); self.browse_btn=browse; browse.clicked.connect(self._browse); outrow.addWidget(self.output,1); outrow.addWidget(browse); outer.addLayout(outrow)
        buttons=QHBoxLayout(); add=QPushButton("Tambah ke antrean"); start=QPushButton("Mulai unduhan"); cancel=QPushButton("Batalkan tugas aktif"); deps=QPushButton("Pusat Dependensi"); self.add_btn=add; self.start_btn=start; self.cancel_btn=cancel; self.deps_btn=deps; add.clicked.connect(self._add_task); start.clicked.connect(self._start_next); cancel.clicked.connect(self._cancel_active); deps.clicked.connect(self._open_dependencies)
        for b in (add,start,cancel,deps): buttons.addWidget(b)
        outer.addLayout(buttons); self.progress=QProgressBar(); self.progress.setValue(0); outer.addWidget(self.progress); self.status=QLabel("Siap. Tambahkan URL untuk memulai."); outer.addWidget(self.status); self.queue_list=QListWidget(); outer.addWidget(self.queue_list,1); qrow=QHBoxLayout(); remove=QPushButton("Hapus tugas terpilih"); retry=QPushButton("Ulangi tugas gagal"); self.remove_btn=remove; self.retry_btn=retry; remove.clicked.connect(self._remove_task); retry.clicked.connect(self._retry_task); qrow.addWidget(remove); qrow.addWidget(retry); outer.addLayout(qrow); self.download_tab=tab; self.tabs.addTab(tab,"Downloader")
    def _build_settings_tab(self):
        tab=QWidget(); layout=QVBoxLayout(tab); self.settings_intro=QLabel("Pengaturan disimpan pada profil pengguna Windows."); layout.addWidget(self.settings_intro); self.ffmpeg=QLineEdit(self.config.data.get("ffmpeg_path","")); self.ffmpeg.setPlaceholderText("Opsional: folder atau path ffmpeg.exe"); self.ffmpeg_label=QLabel("Lokasi FFmpeg"); layout.addWidget(self.ffmpeg_label); layout.addWidget(self.ffmpeg); save=QPushButton("Simpan pengaturan"); self.save_btn=save; save.clicked.connect(self._save_settings); layout.addWidget(save); self.settings_note=QLabel("Log teknis tersedia melalui Pusat Dependensi.\nUnduhan hanya untuk konten yang boleh kamu akses dan simpan."); layout.addWidget(self.settings_note); layout.addStretch(); self.settings_tab=tab; self.tabs.addTab(tab,"Pengaturan")
    def _language_changed(self, _index):
        self.config.data["language"] = self.language_combo.currentData()
        self.config.save()
        self._apply_language()

    def _apply_language(self):
        en = self.language_combo.currentData() == "en"
        self.setWindowTitle("YTDream Downloader — Echidna Edition" if en else "YTDream Downloader — Echidna Edition")
        self.mascot_hint.setText("ECHIDNA • ORIGINAL ASSET" if en else "ECHIDNA • ASET ASLI")
        self.url_label.setText("Media URL" if en else "URL media")
        self.url.setPlaceholderText("Paste a video or playlist URL…" if en else "Tempel URL video atau playlist…")
        self.kind_label.setText("Type" if en else "Jenis")
        self.kind.setItemText(0, "Video")
        self.kind.setItemText(1, "MP3 Audio" if en else "Audio MP3")
        self.format_label.setText("Video format" if en else "Format video")
        self.quality_label.setText("Maximum quality" if en else "Kualitas maksimum")
        qualities = (["Best available", "2160p", "1440p", "1080p", "720p", "480p", "360p"] if en else ["Terbaik tersedia", "2160p", "1440p", "1080p", "720p", "480p", "360p"])
        current_quality = self.quality.currentIndex()
        self.quality.blockSignals(True); self.quality.clear(); self.quality.addItems(qualities); self.quality.setCurrentIndex(max(0, current_quality)); self.quality.blockSignals(False)
        self.playlist.setText("Playlist" if en else "Playlist")
        self.subtitles.setText("Download subtitles" if en else "Unduh subtitle")
        self.auto_subs.setText("Automatic subtitles" if en else "Subtitle otomatis")
        self.browse_btn.setText("Browse…" if en else "Pilih folder")
        self.add_btn.setText("Add to queue" if en else "Tambah ke antrean")
        self.start_btn.setText("Start download" if en else "Mulai unduhan")
        self.cancel_btn.setText("Cancel active task" if en else "Batalkan tugas aktif")
        self.deps_btn.setText("Dependency Center" if en else "Pusat Dependensi")
        self.remove_btn.setText("Remove selected task" if en else "Hapus tugas terpilih")
        self.retry_btn.setText("Retry failed task" if en else "Ulangi tugas gagal")
        self.tabs.setTabText(0, "Downloader")
        self.settings_intro.setText("Settings are saved to your Windows user profile." if en else "Pengaturan disimpan pada profil pengguna Windows.")
        self.ffmpeg_label.setText("FFmpeg location" if en else "Lokasi FFmpeg")
        self.ffmpeg.setPlaceholderText("Optional: folder path or ffmpeg.exe path" if en else "Opsional: folder atau path ffmpeg.exe")
        self.save_btn.setText("Save settings" if en else "Simpan pengaturan")
        self.settings_note.setText("Technical logs are available through Dependency Center.\nOnly download content you are allowed to access and save." if en else "Log teknis tersedia melalui Pusat Dependensi.\nUnduhan hanya untuk konten yang boleh kamu akses dan simpan.")
        self.tabs.setTabText(1, "Settings" if en else "Pengaturan")
        self.progress.setFormat("%p%")
        if self.status.text() in ("Siap. Tambahkan URL untuk memulai.", "Ready. Add a URL to begin."):
            self.status.setText("Ready. Add a URL to begin." if en else "Siap. Tambahkan URL untuk memulai.")
        if hasattr(self, "dependency_dialog") and self.dependency_dialog:
            self.dependency_dialog.apply_language()

    def _browse(self):
        path=QFileDialog.getExistingDirectory(self,"Pilih folder output",self.output.text());
        if path: self.output.setText(path)
    def _save_settings(self):
        self.config.data.update({"output_dir":self.output.text().strip(),"video_format":self.format.currentText(),"quality":self.quality.currentText(),"ffmpeg_path":self.ffmpeg.text().strip()}); self.config.save(); self.status.setText("Pengaturan disimpan.")
    def _add_task(self):
        url=self.url.text().strip()
        if not validate_url(url): QMessageBox.warning(self,"URL tidak valid","Masukkan URL yang diawali http:// atau https://."); return
        task=QueueTask(url=url,kind="audio" if self.kind.currentIndex()==1 else "video",format=self.format.currentText(),quality=self.quality.currentText(),playlist=self.playlist.isChecked(),subtitles=self.subtitles.isChecked(),auto_subtitles=self.auto_subs.isChecked()); self.queue.add(task); self._sync_queue(); self.status.setText("Tugas ditambahkan ke antrean.")
    def _sync_queue(self):
        if not hasattr(self,"queue_list"): return
        self.queue_list.clear()
        for t in self.queue.tasks:
            item=QListWidgetItem(f"[{t.status}] {t.url}" + (f" — {t.error}" if t.error else "")); item.setData(Qt.ItemDataRole.UserRole,t.id); self.queue_list.addItem(item)
    def _start_next(self):
        if self.active_thread and self.active_thread.isRunning(): QMessageBox.information(self,"Unduhan aktif","Tunggu tugas aktif selesai atau batalkan terlebih dahulu."); return
        task=self.queue.next_pending()
        if not task: self.status.setText("Tidak ada tugas yang menunggu."); return
        output=self.output.text().strip()
        if not output: QMessageBox.warning(self,"Folder output","Pilih folder output terlebih dahulu."); return
        task.status="Berjalan"; self._sync_queue(); self.progress.setValue(0); self.active_thread=QThread(self); self.active_worker=DownloadWorker(task.__dict__,output,self.ffmpeg.text().strip()); self.active_worker.moveToThread(self.active_thread); self.active_thread.started.connect(self.active_worker.run); self.active_worker.progress.connect(self._on_progress); self.active_worker.stage.connect(self.status.setText); self.active_worker.finished.connect(lambda msg,t=task:self._task_done(t,msg)); self.active_worker.failed.connect(lambda msg,t=task:self._task_failed(t,msg)); self.active_worker.finished.connect(self.active_thread.quit); self.active_worker.failed.connect(self.active_thread.quit); self.active_thread.finished.connect(self._worker_cleanup); self.active_thread.start()
    def _on_progress(self,data):
        total=data.get("total"); done=data.get("downloaded",0); self.progress.setValue(int(done*100/total) if total else 0)
        if data.get("filename"): self.status.setText(Path(data["filename"]).name)
    def _task_done(self,task,msg): task.status="Selesai"; self.status.setText(msg); self.progress.setValue(100); self._sync_queue()
    def _task_failed(self,task,msg): task.status="Dibatalkan" if "batal" in msg.lower() else "Gagal"; task.error=msg; self.status.setText(f"Tugas {task.status.lower()}: {msg}"); logging.error("Download failed: %s",msg); self._sync_queue()
    def _worker_cleanup(self): self.active_worker=None; self.active_thread=None
    def _cancel_active(self):
        if self.active_worker: self.active_worker.cancel(); self.status.setText("Permintaan pembatalan dikirim; menunggu proses berhenti…")
        else: self.status.setText("Tidak ada tugas aktif.")
    def _remove_task(self):
        item=self.queue_list.currentItem()
        if not item:return
        if self.queue.remove(item.data(Qt.ItemDataRole.UserRole)): self._sync_queue()
        else: QMessageBox.information(self,"Tugas tidak dapat dihapus","Hanya tugas menunggu, gagal, atau dibatalkan yang dapat dihapus.")
    def _retry_task(self):
        item=self.queue_list.currentItem()
        if not item:return
        task=next((t for t in self.queue.tasks if t.id==item.data(Qt.ItemDataRole.UserRole)),None)
        if task and task.status in ("Gagal","Dibatalkan"): task.status="Menunggu"; task.error=""; self._sync_queue(); self._start_next()
    def _open_dependencies(self):
        dlg=DependencyDialog(self.config,self); dlg.exec(); self.ffmpeg.setText(self.config.data.get("ffmpeg_path",""))
    def closeEvent(self,event):
        if self.active_worker: QMessageBox.warning(self,"Unduhan sedang berjalan","Batalkan dan tunggu tugas aktif berhenti sebelum menutup aplikasi."); event.ignore(); return
        self._save_settings(); event.accept()
