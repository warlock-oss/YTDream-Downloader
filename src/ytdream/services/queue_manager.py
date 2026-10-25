from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
@dataclass
class QueueTask:
    url: str
    kind: str="video"
    format: str="MP4"
    quality: str="Terbaik tersedia"
    playlist: bool=False
    subtitles: bool=False
    auto_subtitles: bool=False
    id: str=field(default_factory=lambda: str(uuid4()))
    status: str="Menunggu"
    error: str=""
class QueueManager:
    def __init__(self): self.tasks: list[QueueTask]=[]
    def add(self, task: QueueTask): self.tasks.append(task); return task
    def remove(self, task_id: str) -> bool:
        for i,t in enumerate(self.tasks):
            if t.id==task_id and t.status in ("Menunggu","Gagal","Dibatalkan"): self.tasks.pop(i); return True
        return False
    def next_pending(self): return next((t for t in self.tasks if t.status=="Menunggu"), None)
