import os
import sys
import subprocess
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import Optional


class PlatformInfo:
    is_windows: bool = sys.platform == "win32"
    is_linux: bool = sys.platform == "linux"

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.bin_dir = self.base_dir / "bin"
        self.lists_dir = self.base_dir / "lists"
        self.utils_dir = self.base_dir / "utils"
        self.strategies_dir = self.base_dir / "gui" / "strategies"
        self.config_dir = self._get_config_dir()

        if self.is_windows:
            self.binary = self.bin_dir / "winws.exe"
            self.iptables_bin = None
        else:
            self.binary = self.bin_dir / "nfqws"
            self.nftables_bin = shutil.which("nft") or shutil.which("iptables")
            self.iptables_bin = shutil.which("iptables")

    def _get_config_dir(self) -> Path:
        if self.is_windows:
            base = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        else:
            base = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        return Path(base) / "mangopret"

    def ensure_dirs(self):
        for d in [self.config_dir, self.bin_dir, self.lists_dir, self.utils_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def is_binary_present(self) -> bool:
        return self.binary.exists()

    def get_winws_args(self, wf_tcp: str, wf_udp: str, game_filter_tcp: str, game_filter_udp: str) -> list:
        args = []
        tcp_parts = [p.strip() for p in wf_tcp.split(",") if p.strip()]
        udp_parts = [p.strip() for p in wf_udp.split(",") if p.strip()]
        if game_filter_tcp and game_filter_tcp != "12":
            tcp_parts.append(game_filter_tcp)
        if game_filter_udp and game_filter_udp != "12":
            udp_parts.append(game_filter_udp)
        if tcp_parts:
            args.append(f"--wf-tcp={','.join(tcp_parts)}")
        if udp_parts:
            args.append(f"--wf-udp={','.join(udp_parts)}")
        return args

    def get_nfqueue_args(self, queue_num: str = "200") -> list:
        return ["--queue-num", queue_num]

    def build_iptables_rules(self, wf_tcp: str, wf_udp: str, queue_num: str = "200") -> list:
        rules = []
        tcp_ports = self._expand_ports(wf_tcp)
        udp_ports = self._expand_ports(wf_udp)
        for p in tcp_ports:
            rules.append(f"iptables -t mangle -A FORWARD -p tcp --dport {p} -j NFQUEUE --queue-num {queue_num}")
            rules.append(f"iptables -t mangle -A OUTPUT -p tcp --dport {p} -j NFQUEUE --queue-num {queue_num}")
        for p in udp_ports:
            rules.append(f"iptables -t mangle -A FORWARD -p udp --dport {p} -j NFQUEUE --queue-num {queue_num}")
            rules.append(f"iptables -t mangle -A OUTPUT -p udp --dport {p} -j NFQUEUE --queue-num {queue_num}")
        return rules

    @staticmethod
    def _expand_ports(spec: str) -> list:
        ports = []
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                lo, hi = part.split("-", 1)
                ports.extend(range(int(lo), int(hi) + 1))
            else:
                ports.append(int(part))
        return ports

    def download_zapret(self, dest_dir: Optional[Path] = None, callback=None) -> bool:
        dest = dest_dir or self.bin_dir
        dest.mkdir(parents=True, exist_ok=True)

        repo_url = "https://github.com/bol-van/zapret"
        releases_url = "https://api.github.com/repos/bol-van/zapret/releases/latest"

        try:
            import urllib.request
            import json

            if callback:
                callback("Checking latest zapret release...")

            req = urllib.request.Request(releases_url, headers={"User-Agent": "Mangopret"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            tag = data.get("tag_name", "")
            if not tag:
                if callback:
                    callback("Failed to get latest release tag")
                return False

            if self.is_linux:
                asset_name = f"zapret-linux-{tag.lstrip('v')}.tar.gz"
            else:
                asset_name = f"zapret-win-bundle-{tag.lstrip('v')}.zip"

            asset_url = None
            for asset in data.get("assets", []):
                name = asset["name"].lower()
                if self.is_linux and name.endswith(".tar.gz") and "linux" in name:
                    asset_url = asset["browser_download_url"]
                    break
                elif self.is_windows and name.endswith(".zip") and ("win" in name or "bundle" in name):
                    asset_url = asset["browser_download_url"]
                    break

            if not asset_url:
                for asset in data.get("assets", []):
                    name = asset["name"].lower()
                    if self.is_linux and name.endswith(".tar.gz"):
                        asset_url = asset["browser_download_url"]
                        break
                    elif self.is_windows and name.endswith(".zip"):
                        asset_url = asset["browser_download_url"]
                        break

            if not asset_url:
                if callback:
                    callback("No suitable release asset found")
                return False

            if callback:
                callback(f"Downloading {asset_url}...")

            tmp_path = dest / ("zapret_download.tmp")
            urllib.request.urlretrieve(asset_url, tmp_path)

            if callback:
                callback("Extracting...")

            if asset_url.endswith(".zip"):
                with zipfile.ZipFile(tmp_path, "r") as zf:
                    zf.extractall(dest)
            elif asset_url.endswith(".tar.gz") or asset_url.endswith(".tgz"):
                with tarfile.open(tmp_path, "r:gz") as tf:
                    tf.extractall(dest)

            tmp_path.unlink(missing_ok=True)

            if self.is_linux:
                nfqws = dest / "nfqws"
                if not nfqws.exists():
                    for f in dest.rglob("nfqws"):
                        shutil.copy2(f, nfqws)
                        break
                if nfqws.exists():
                    nfqws.chmod(0o755)

                nft = dest / "nftables" / "zapret"
                if nft.exists():
                    nft.chmod(0o755)

            if callback:
                callback("Done!")
            return True

        except Exception as e:
            if callback:
                callback(f"Error: {e}")
            return False

    def start_service(self, strategy_name: str, args: list) -> Optional[subprocess.Popen]:
        cmd = [str(self.binary)] + args

        if self.is_windows:
            return subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS,
                cwd=str(self.bin_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            return subprocess.Popen(
                cmd,
                cwd=str(self.bin_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def stop_process(self, proc: Optional[subprocess.Popen]):
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        except Exception:
            pass

    def kill_all(self):
        if self.is_windows:
            subprocess.run(
                ["taskkill", "/IM", "winws.exe", "/F"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            subprocess.run(["pkill", "-f", "nfqws"], capture_output=True)
            self._cleanup_iptables()

    def _cleanup_iptables(self):
        if not self.is_linux:
            return
        try:
            result = subprocess.run(
                ["iptables", "-t", "mangle", "-L", "OUTPUT", "--line-numbers"],
                capture_output=True, text=True, timeout=5,
            )
            for line in reversed(result.stdout.splitlines()):
                parts = line.split()
                if len(parts) >= 1 and parts[0].isdigit():
                    subprocess.run(
                        ["iptables", "-t", "mangle", "-D", "OUTPUT", parts[0]],
                        capture_output=True, timeout=5,
                    )
            result = subprocess.run(
                ["iptables", "-t", "mangle", "-L", "FORWARD", "--line-numbers"],
                capture_output=True, text=True, timeout=5,
            )
            for line in reversed(result.stdout.splitlines()):
                parts = line.split()
                if len(parts) >= 1 and parts[0].isdigit():
                    subprocess.run(
                        ["iptables", "-t", "mangle", "-D", "FORWARD", parts[0]],
                        capture_output=True, timeout=5,
                    )
        except Exception:
            pass

    def is_process_running(self, name: str = None) -> bool:
        if name is None:
            name = "winws.exe" if self.is_windows else "nfqws"
        try:
            if self.is_windows:
                r = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {name}"],
                    capture_output=True, text=True, timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                return name.lower() in r.stdout.lower()
            else:
                r = subprocess.run(["pgrep", "-f", name], capture_output=True, timeout=5)
                return r.returncode == 0
        except Exception:
            return False

    def get_service_status(self) -> str:
        if self.is_windows:
            try:
                r = subprocess.run(
                    ["sc", "query", "zapret"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if "RUNNING" in r.stdout:
                    return "running"
                elif "STOPPED" in r.stdout:
                    return "stopped"
            except Exception:
                pass
            return "not_installed"
        else:
            try:
                r = subprocess.run(
                    ["systemctl", "is-active", "zapret"],
                    capture_output=True, text=True, timeout=5,
                )
                return r.stdout.strip()
            except Exception:
                return "not_installed"
