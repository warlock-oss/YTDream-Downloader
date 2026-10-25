import re

_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)

def validate_url(url: str) -> bool:
    """Basic URL shape validation; the downloader validates actual source support later."""
    return bool(_URL_RE.match(url.strip()))
