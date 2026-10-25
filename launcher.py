"""Package-safe entry point for PyInstaller builds."""
from ytdream.main import main

if __name__ == "__main__":
    raise SystemExit(main())
