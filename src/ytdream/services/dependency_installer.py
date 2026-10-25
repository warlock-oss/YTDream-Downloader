from __future__ import annotations
import os, subprocess, sys, urllib.request, zipfile, tempfile, shutil
from pathlib import Path
from .dependency_checker import DependencyStatus
from ..utils.paths import app_root

class DependencyInstallError(RuntimeError): pass

def install_python_package(package: str, progress=None) -> None:
    # Do not mutate a global Python installation from the dependency center.
    if not (sys.prefix != getattr(sys, "base_prefix", sys.prefix) or getattr(sys, "frozen", False)):
        raise DependencyInstallError("Instalasi paket diblokir karena Python bukan virtual environment. Jalankan setup.bat untuk membuat .venv terlebih dahulu.")
    cmd=[sys.executable, "-m", "pip", "install", "--disable-pip-version-check", package]
    p=subprocess.run(cmd, capture_output=True, text=True, timeout=900, check=False)
    if p.returncode: raise DependencyInstallError((p.stderr or p.stdout or "pip gagal tanpa detail")[-2500:])

def install_ffmpeg(progress=None) -> Path:
    """Fetch a Windows build from BtbN's GitHub releases API; never run the downloaded binary automatically."""
    if sys.platform != "win32": raise DependencyInstallError("Pemasangan FFmpeg otomatis ini hanya tersedia di Windows.")
    import json
    api="https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
    req=urllib.request.Request(api, headers={"User-Agent":"YTDream-Downloader/0.1", "Accept":"application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r: release=json.load(r)
    except Exception as e: raise DependencyInstallError(f"Tidak dapat membaca rilis FFmpeg tepercaya: {e}") from e
    assets=release.get("assets", [])
    # BtbN names releases differently from Gyan.dev: typically
    # ffmpeg-master-latest-win64-gpl.zip, not *win64-gpl-essentials.zip*.
    def suitable_asset(item):
        name = item.get("name", "").lower()
        if not name.endswith(".zip") or "win64" not in name or "gpl" not in name:
            return False
        if any(token in name for token in ("shared", "debug", "symbols", "lgpl", "dev")):
            return False
        return True
    asset=next((a for a in assets if suitable_asset(a)), None)
    if not asset:
        choices = ", ".join(a.get("name", "") for a in assets if "win64" in a.get("name", "").lower())
        raise DependencyInstallError(
            "Arsip FFmpeg Windows yang sesuai tidak ditemukan pada rilis BtbN terbaru. "
            + (f"Arsip Windows yang tersedia: {choices}" if choices else "Rilis tidak memuat arsip Windows yang dikenali.")
        )
    dest=app_root()/"tools"/"ffmpeg"; dest.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(suffix=".zip"); os.close(fd); temp=Path(tmp)
    try:
        req=urllib.request.Request(asset["browser_download_url"], headers={"User-Agent":"YTDream-Downloader/0.1"})
        with urllib.request.urlopen(req, timeout=60) as r, temp.open("wb") as out:
            total=int(r.headers.get("Content-Length", 0)); done=0
            while True:
                chunk=r.read(1024*1024)
                if not chunk: break
                out.write(chunk); done+=len(chunk)
                if progress: progress(done, total)
        # GitHub release asset does not always publish a checksum. Refuse silent execution;
        # extraction is limited to expected ffmpeg/ffprobe binaries.
        with zipfile.ZipFile(temp) as z:
            members=[m for m in z.namelist() if Path(m).name.lower() in ("ffmpeg.exe", "ffprobe.exe")]
            if not {"ffmpeg.exe", "ffprobe.exe"}.issubset({Path(m).name.lower() for m in members}): raise DependencyInstallError("Arsip tidak memuat ffmpeg.exe dan ffprobe.exe lengkap.")
            for member in members:
                info=z.getinfo(member)
                if info.file_size > 200*1024*1024: raise DependencyInstallError("Ukuran file executable di dalam arsip tidak wajar.")
                target=dest/Path(member).name
                with z.open(member) as src, target.open("wb") as out: shutil.copyfileobj(src, out)
        return dest
    except (OSError, zipfile.BadZipFile, urllib.error.URLError) as e: raise DependencyInstallError(f"Unduhan atau ekstraksi FFmpeg gagal: {e}") from e
    finally: temp.unlink(missing_ok=True)
