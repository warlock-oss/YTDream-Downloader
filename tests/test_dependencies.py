from ytdream.services.dependency_checker import check_dependencies

def test_dependency_checker_returns_expected_components():
    rows=check_dependencies()
    names={r.name for r in rows}
    assert {"Python runtime","PySide6","yt-dlp","FFmpeg","FFprobe","Resource aplikasi"} <= names
    assert all(r.status for r in rows)
