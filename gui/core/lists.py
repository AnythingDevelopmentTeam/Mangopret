import os
import subprocess
from pathlib import Path
from typing import Callable
from core.log import get_logger

logger = get_logger(__name__)

_WIN_CREATE_NO_WINDOW = 0x08000000


class ListManager:
    def __init__(self, lists_dir: str, utils_dir: str) -> None:
        self.lists_dir = Path(lists_dir)
        self.utils_dir = Path(utils_dir)
        self._ensure_user_lists()

    def _ensure_user_lists(self) -> None:
        self.lists_dir.mkdir(parents=True, exist_ok=True)

        ipset_user = self.lists_dir / "ipset-exclude-user.txt"
        if not ipset_user.exists():
            ipset_user.write_text("203.0.113.113/32\n", encoding="utf-8")

        general_user = self.lists_dir / "list-general-user.txt"
        if not general_user.exists():
            general_user.write_text(
                "# Never leave this file empty\ndomain.example.abc\n", encoding="utf-8"
            )

        exclude_user = self.lists_dir / "list-exclude-user.txt"
        if not exclude_user.exists():
            exclude_user.write_text("domain.example.abc\n", encoding="utf-8")

    def get_list_files(self) -> list[str]:
        files: list[str] = []
        for f in sorted(self.lists_dir.iterdir()):
            if f.suffix == ".txt" and f.is_file():
                files.append(f.name)
        return files

    def get_domain_list_files(self) -> list[str]:
        return [f for f in self.get_list_files() if f.startswith("list-")]

    def get_ipset_list_files(self) -> list[str]:
        return [f for f in self.get_list_files() if f.startswith("ipset-")]

    def read_list(self, filename: str) -> str:
        path = self.lists_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def write_list(self, filename: str, content: str) -> None:
        path = self.lists_dir / filename
        path.write_text(content.rstrip("\n") + "\n", encoding="utf-8")

    def add_entry(self, filename: str, entry: str) -> None:
        content = self.read_list(filename)
        entry = entry.strip()
        if entry and entry not in content:
            content += entry + "\n"
            self.write_list(filename, content)

    def remove_entry(self, filename: str, entry: str) -> None:
        content = self.read_list(filename)
        lines = content.splitlines()
        lines = [l for l in lines if l.strip() != entry.strip()]
        self.write_list(filename, "\n".join(lines))

    def update_ipset(self, callback: Callable[[str], None] | None = None) -> bool:
        url = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/refs/heads/main/.service/ipset-service.txt"
        dest = self.lists_dir / "ipset-all.txt"
        try:
            import urllib.request
            if callback:
                callback("Downloading ipset...")
            urllib.request.urlretrieve(url, dest)
            if callback:
                callback("IPSet updated successfully")
            return True
        except Exception as exc:
            msg = f"Failed to update IPSet: {exc}"
            if callback:
                callback(msg)
            logger.warning(msg)
            return False

    def update_hosts(self, callback: Callable[[str], None] | None = None) -> bool:
        url = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/refs/heads/main/.service/hosts"
        if os.name == "nt":
            hosts_path = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "drivers" / "etc" / "hosts"
        else:
            hosts_path = Path("/etc/hosts")

        try:
            import urllib.request
            import tempfile
            if callback:
                callback("Downloading hosts file...")
            tmp = Path(tempfile.mktemp(suffix=".txt"))
            urllib.request.urlretrieve(url, tmp)

            content = tmp.read_text(encoding="utf-8")
            first_line = content.splitlines()[0] if content.splitlines() else ""
            last_line = content.splitlines()[-1] if content.splitlines() else ""

            needs_update = False
            if hosts_path.exists():
                existing = hosts_path.read_text(encoding="utf-8")
                if first_line and first_line not in existing:
                    needs_update = True
                if last_line and last_line not in existing:
                    needs_update = True
            else:
                needs_update = True

            tmp.unlink(missing_ok=True)

            if needs_update:
                if callback:
                    callback(f"Hosts file needs update. New content available at: {url}")
                return True
            else:
                if callback:
                    callback("Hosts file is up to date")
                return False
        except Exception as exc:
            msg = f"Failed to check hosts: {exc}"
            if callback:
                callback(msg)
            logger.warning(msg)
            return False

    def update_strategies(self, strategies_dir: str, branch: str = "main", callback: Callable[[str], None] | None = None) -> bool:
        url = f"https://api.github.com/repos/AnythingDevelopmentTeam/Mangopret/contents/gui/strategies?ref={branch}"
        dest = Path(strategies_dir)
        try:
            import urllib.request
            import json

            if callback:
                callback("Fetching strategy list...")
            req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                files = json.loads(resp.read().decode())

            dest.mkdir(parents=True, exist_ok=True)
            updated = 0
            for item in files:
                if item["name"].endswith(".strategy"):
                    if callback:
                        callback(f"Downloading {item['name']}...")
                    file_url = item["download_url"]
                    local = dest / item["name"]
                    urllib.request.urlretrieve(file_url, local)
                    updated += 1

            if callback:
                callback(f"Updated {updated} strategies from branch '{branch}'")
            return True
        except Exception as exc:
            msg = f"Failed to update strategies: {exc}"
            if callback:
                callback(msg)
            logger.warning(msg)
            return False

    def run_diagnostics(self, is_windows: bool = True) -> str:
        results: list[str] = []

        if is_windows:
            try:
                r = subprocess.run(
                    ["sc", "query", "BFE"],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                )
                if "RUNNING" in r.stdout:
                    results.append("[OK] Base Filtering Engine is running")
                else:
                    results.append("[FAIL] Base Filtering Engine is not running")
            except Exception as exc:
                results.append("[FAIL] Could not check BFE")
                logger.debug("BFE check failed: %s", exc)

            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                )
                proxy_enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if proxy_enabled:
                    results.append("[WARN] System proxy is enabled - may conflict with DPI bypass")
                else:
                    results.append("[OK] System proxy is disabled")
                winreg.CloseKey(key)
            except Exception as exc:
                results.append("[OK] Could not check proxy status")
                logger.debug("Proxy check failed: %s", exc)

            try:
                r = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq AdguardSvc.exe"],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                )
                if "AdguardSvc.exe" in r.stdout:
                    results.append("[WARN] Adguard is running - may cause conflicts")
                else:
                    results.append("[OK] Adguard not detected")
            except Exception as exc:
                logger.debug("Adguard check failed: %s", exc)
        else:
            results.append("[OK] Running on Linux")
            try:
                r = subprocess.run(["which", "nft"], capture_output=True, timeout=5)
                if r.returncode == 0:
                    results.append("[OK] nftables found")
                else:
                    r2 = subprocess.run(["which", "iptables"], capture_output=True, timeout=5)
                    if r2.returncode == 0:
                        results.append("[OK] iptables found")
                    else:
                        results.append("[FAIL] Neither nftables nor iptables found")
            except Exception as exc:
                logger.debug("Firewall check failed: %s", exc)

            try:
                r = subprocess.run(["id"], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
                if "uid=0" in r.stdout:
                    results.append("[OK] Running as root")
                else:
                    results.append("[WARN] Not running as root - may need sudo for iptables")
            except Exception as exc:
                logger.debug("Root check failed: %s", exc)

        return "\n".join(results)
