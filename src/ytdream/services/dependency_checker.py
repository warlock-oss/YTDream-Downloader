from __future__ import annotations

import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from ..utils.paths import app_root


@dataclass
class DependencyStatus:
    name: str
    required: str
    status: str
    detected: str = "—"
    detail: str = ""
    required_component: bool = True


def _candidate_paths(command: str, configured_path: str = "") -> list[Path]:
    """Find FFmpeg tools from settings, app-local folders, common manual installs, and PATH."""
    suffix = ".exe" if sys.platform == "win32" else ""
    filename = f"{command}{suffix}"
    candidates: list[Path] = []

    if configured_path:
        configured = Path(configured_path).expanduser()
        if configured.is_dir():
            candidates.append(configured / filename)
        elif configured.is_file():
            if configured.name.lower() in (filename.lower(), command.lower()):
                candidates.append(configured)
            else:
                candidates.append(configured.parent / filename)
        elif configured.exists():
            candidates.append(configured / filename)

    root = app_root()
    candidates.extend([
        root / "tools" / "ffmpeg" / filename,
        root / "ffmpeg" / filename,
        root / "tools" / filename,
        Path("C:/Tools/ffmpeg") / filename,
    ])

    # Common manually extracted Windows builds, including the user's Downloads folder.
    if sys.platform == "win32":
        downloads = Path.home() / "Downloads"
        try:
            for folder in sorted(downloads.glob("ffmpeg*/bin"), reverse=True):
                candidates.append(folder / filename)
            for folder in sorted(downloads.glob("ffmpeg*"), reverse=True):
                if folder.is_dir() and folder.name.lower().endswith("_build"):
                    candidates.append(folder / filename)
        except OSError:
            pass

    located = shutil.which(command)
    if located:
        candidates.append(Path(located))

    # Preserve order while eliminating duplicate paths.
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def find_ffmpeg_directory(configured_path: str = "") -> str:
    """Return the directory containing a working ffmpeg.exe, or an empty string."""
    for candidate in _candidate_paths("ffmpeg", configured_path):
        if candidate.is_file() and _command_version_at_path(candidate):
            return str(candidate.parent)
    return ""


def _command_version_at_path(candidate: Path) -> str | None:
    try:
        if not candidate.is_file():
            return None
        proc = subprocess.run(
            [str(candidate), "-version"], capture_output=True, text=True, timeout=8,
            check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        output = (proc.stdout or proc.stderr or "").splitlines()
        return output[0][:160] if proc.returncode == 0 and output else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _command_version(command: str, configured_path: str = "") -> str | None:
    for candidate in _candidate_paths(command, configured_path):
        detected = _command_version_at_path(candidate)
        if detected:
            return detected
    return None


def check_dependencies(bundled: bool = False, ffmpeg_path: str = "") -> list[DependencyStatus]:
    result: list[DependencyStatus] = []
    python_ok = (3, 10) <= sys.version_info[:2] < (3, 14)
    result.append(DependencyStatus(
        "Python runtime",
        "Bundled" if bundled else ">=3.10,<3.14",
        "Sudah dibundel" if bundled else ("Siap digunakan" if python_ok else "Versi tidak kompatibel"),
        sys.version.split()[0],
        "Diperlukan saat menjalankan dari source; executable membawa runtime sendiri.",
    ))

    for package, label, module in (("PySide6", "PySide6", "PySide6"), ("yt-dlp", "yt-dlp", "yt_dlp")):
        available = importlib.util.find_spec(module) is not None
        try:
            version = importlib.metadata.version(package) if available else "—"
        except importlib.metadata.PackageNotFoundError:
            version = "Tersedia; metadata versi tidak ditemukan" if available else "—"
        result.append(DependencyStatus(
            label, "Versi sesuai requirements.txt", "Siap digunakan" if available else "Belum tersedia",
            version, "Paket Python aplikasi; diperiksa melalui kemampuan import dan metadata versi.",
        ))

    for command, label in (("ffmpeg", "FFmpeg"), ("ffprobe", "FFprobe")):
        detected = _command_version(command, ffmpeg_path)
        result.append(DependencyStatus(
            label, "Versi kompatibel", "Siap digunakan" if detected else "Belum tersedia",
            detected or "—",
            "Lokasi diperiksa dari pengaturan, folder aplikasi, lokasi umum, Downloads, dan PATH.",
        ))

    asset_root = app_root() / "assets"
    mascot = asset_root / "images" / "echidna.png"
    resource_ok = asset_root.exists()
    resource_detail = "Maskot ditemukan." if mascot.is_file() else "Folder assets tersedia; maskot echidna.png belum ditemukan (opsional)."
    result.append(DependencyStatus(
        "Resource aplikasi", "Maskot dan konfigurasi", "Siap digunakan" if resource_ok else "Periksa resource",
        "Tersedia" if resource_ok else "—", resource_detail, False,
    ))
    return result
