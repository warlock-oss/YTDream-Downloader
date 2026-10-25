from __future__ import annotations
import json
from pathlib import Path
from PySide6.QtCore import QStandardPaths

class AppConfig:
    def __init__(self):
        base = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
        base.mkdir(parents=True, exist_ok=True); self.path = base / "settings.json"
        self.data = {"output_dir": str(Path.home() / "Downloads"), "video_format": "MP4", "audio_format": "MP3", "quality": "Terbaik tersedia", "max_parallel": 1, "ffmpeg_path": "", "language": "id"}
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8")); self.data.update(loaded)
        except (OSError, ValueError): pass
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp"); tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"); tmp.replace(self.path)
