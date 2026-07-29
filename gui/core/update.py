import re
import urllib.request

from gui import APP_VERSION

CHECKUPDATE_URL = "https://raw.githubusercontent.com/AnythingDevelopmentTeam/Mangopret/main/checkupdate"


def check_mangopret_update() -> tuple[str, str, str] | None:
    """Fetch latest version info. Returns (current, latest, hash) or None."""
    try:
        req = urllib.request.Request(
            CHECKUPDATE_URL, headers={"User-Agent": "Mangopret"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8")
    except Exception:
        return None

    m = re.search(r'^LAST_VERSION\s*=\s*"(.+?)"', text, re.MULTILINE)
    if not m:
        return None
    latest = m.group(1)

    m = re.search(r'^VERSION_HASH\s*=\s*"(.+?)"', text, re.MULTILINE)
    vhash = m.group(1) if m else ""

    return (APP_VERSION, latest, vhash)
