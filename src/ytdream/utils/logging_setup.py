import logging
from logging.handlers import RotatingFileHandler
from .paths import log_dir

def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers: return
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh = RotatingFileHandler(log_dir() / "ytdream.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt); root.addHandler(fh)
