from __future__ import annotations
import os, sys
from pathlib import Path

def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]

def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", app_root()))
    return base.joinpath(*parts)

def data_dir() -> Path:
    base = Path(os.getenv("LOCALAPPDATA", Path.home())) / "YTDreamDownloader"
    base.mkdir(parents=True, exist_ok=True)
    return base

def log_dir() -> Path:
    p = data_dir() / "logs"; p.mkdir(parents=True, exist_ok=True); return p
