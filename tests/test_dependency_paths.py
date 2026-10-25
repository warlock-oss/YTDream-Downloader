from pathlib import Path

from ytdream.services import dependency_checker as checker


def test_configured_ffmpeg_directory_is_used(tmp_path, monkeypatch):
    suffix = ".exe" if checker.sys.platform == "win32" else ""
    ffmpeg = tmp_path / f"ffmpeg{suffix}"
    ffprobe = tmp_path / f"ffprobe{suffix}"
    ffmpeg.write_bytes(b"test executable placeholder")
    ffprobe.write_bytes(b"test executable placeholder")

    monkeypatch.setattr(checker, "_command_version_at_path", lambda path: "ffmpeg version test" if path.is_file() else None)
    assert checker.find_ffmpeg_directory(str(tmp_path)) == str(tmp_path)
    assert checker._command_version("ffprobe", str(tmp_path)) == "ffmpeg version test"


def test_ffmpeg_path_can_be_an_executable_file(tmp_path, monkeypatch):
    suffix = ".exe" if checker.sys.platform == "win32" else ""
    ffmpeg = tmp_path / f"ffmpeg{suffix}"
    ffprobe = tmp_path / f"ffprobe{suffix}"
    ffmpeg.write_bytes(b"test executable placeholder")
    ffprobe.write_bytes(b"test executable placeholder")

    monkeypatch.setattr(checker, "_command_version_at_path", lambda path: f"version from {path.name}" if path.is_file() else None)
    assert checker._command_version("ffmpeg", str(ffmpeg)) == f"version from ffmpeg{suffix}"
    assert checker._command_version("ffprobe", str(ffmpeg)) == f"version from ffprobe{suffix}"


def test_dependency_check_includes_ffmpeg_and_ffprobe():
    statuses = checker.check_dependencies()
    by_name = {status.name: status for status in statuses}
    assert "FFmpeg" in by_name
    assert "FFprobe" in by_name
    assert by_name["FFmpeg"].status
    assert by_name["FFprobe"].status
