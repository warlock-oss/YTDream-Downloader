from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from ..utils.validation import validate_url

class DownloadWorker(QObject):
    progress=Signal(dict); finished=Signal(str); failed=Signal(str); stage=Signal(str)
    def __init__(self, task: dict, output_dir: str, ffmpeg_path: str=""):
        super().__init__(); self.task=task; self.output_dir=output_dir; self.ffmpeg_path=ffmpeg_path; self._cancel=False; self._ydl=None
    @Slot()
    def run(self):
        try:
            import yt_dlp
            if not validate_url(self.task["url"]): raise ValueError("URL tidak valid. Gunakan alamat yang diawali http:// atau https://.")
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            def hook(d):
                if self._cancel: raise InterruptedError("Unduhan dibatalkan oleh pengguna.")
                self.progress.emit({"status":d.get("status", "downloading"),"downloaded":d.get("downloaded_bytes",0),"total":d.get("total_bytes") or d.get("total_bytes_estimate"),"filename":d.get("filename", "")})
            opts={"outtmpl":str(Path(self.output_dir)/"%(title).180B [%(id)s].%(ext)s"),"noplaylist":not self.task.get("playlist", False),"progress_hooks":[hook],"quiet":True,"no_warnings":True,"windowsfilenames":True,"ignoreerrors":False,"continuedl":True,"overwrites":False}
            if self.ffmpeg_path: opts["ffmpeg_location"]=self.ffmpeg_path
            kind=self.task.get("kind", "video")
            if kind=="audio": opts.update({"format":"bestaudio/best","postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]})
            else:
                ext=self.task.get("format", "MP4").lower(); opts["merge_output_format"]=ext
                quality=self.task.get("quality", "Terbaik tersedia")
                if quality not in ("Terbaik tersedia", "Best available"):
                    height=int(quality.replace("p", "")); opts["format"]=f"bv*[height<={height}]+ba/b[height<={height}]/best"
                else: opts["format"]="bv*+ba/b"
            if self.task.get("subtitles"): opts.update({"writesubtitles":True,"writeautomaticsub":bool(self.task.get("auto_subtitles", False)),"subtitleslangs":["all"],"subtitlesformat":"srt/vtt/best"})
            self.stage.emit("Mengambil informasi media…")
            with yt_dlp.YoutubeDL(opts) as ydl:
                self._ydl=ydl; self.stage.emit("Mengunduh media…"); ydl.download([self.task["url"]])
            if self._cancel: self.failed.emit("Unduhan dibatalkan.")
            else: self.finished.emit("Unduhan selesai.")
        except InterruptedError as e: self.failed.emit(str(e))
        except Exception as e: self.failed.emit(str(e) or e.__class__.__name__)
    def cancel(self): self._cancel=True
