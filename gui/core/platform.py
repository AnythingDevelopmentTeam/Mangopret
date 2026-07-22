import os
import sys
import subprocess
import shutil
import zipfile
import tarfile
import urllib.request
import json
import tempfile
from pathlib import Path
from typing import Optional

ZAPRET_VERSION = "72.13"
ZAPRET_URL = f"https://github.com/bol-van/zapret/releases/download/v{ZAPRET_VERSION}/zapret-v{ZAPRET_VERSION}.tar.gz"
ZAPRET_DIR = Path("/opt/zapret")

_WIN_CREATE_NO_WINDOW = 0x08000000
_WIN_BELOW_NORMAL_PRIORITY = 0x00008000


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
        self.zapret_dir = ZAPRET_DIR

        if self.is_windows:
            self.binary = self.bin_dir / "winws.exe"
            self.iptables_bin = None
        else:
            self.nftables_bin = shutil.which("nft") or shutil.which("iptables")
            self.iptables_bin = shutil.which("iptables")
            self._resolve_binary()

    def _resolve_binary(self):
        zapret_dirs = [
            self.zapret_dir / "nfq" / "nfqws",
            self.zapret_dir / "bin" / "nfqws",
            self.zapret_dir / "binaries" / "linux-x86_64" / "nfqws",
        ]
        local_bin = self.bin_dir / "nfqws"

        for zp in zapret_dirs:
            if zp.exists():
                self.binary = zp
                return

        if local_bin.exists():
            self.binary = local_bin
        else:
            self.binary = zapret_dirs[0]

    def _get_config_dir(self) -> Path:
        if self.is_windows:
            base = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        else:
            base = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        return Path(base) / "mangopret"

    @staticmethod
    def _find_terminal() -> str:
        for name in ["x-terminal-emulator", "xdg-terminal-exec"]:
            path = shutil.which(name)
            if path:
                return path
        return ""

    @staticmethod
    def _is_graphical() -> bool:
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    @staticmethod
    def _is_root() -> bool:
        return os.geteuid() == 0

    def ensure_dirs(self):
        for d in [self.config_dir, self.bin_dir, self.lists_dir, self.utils_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def is_binary_present(self) -> bool:
        return self.binary.exists()

    def is_zapret_installed(self) -> bool:
        return (self.zapret_dir / "install_easy.sh").exists() or (self.zapret_dir / "config").exists()

    # ------------------------------------------------------------------ install
    def install_zapret(self, callback=None) -> bool:
        if not self.is_linux:
            return self._install_zapret_windows(callback)

        try:
            tmpdir = Path(tempfile.mkdtemp(prefix="mangopret_"))

            if callback:
                callback(f"Downloading zapret v{ZAPRET_VERSION} ...")

            archive = tmpdir / "zapret.tar.gz"
            urllib.request.urlretrieve(ZAPRET_URL, archive)

            if callback:
                callback("Extracting ...")

            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(tmpdir)

            src = None
            for d in tmpdir.iterdir():
                if d.is_dir() and d.name.startswith("zapret"):
                    src = d
                    break
            if src is None:
                src = tmpdir

            if callback:
                callback(f"Installing to {self.zapret_dir} ...")

            installer = Path(__file__).parent.parent.parent / "silent_install.sh"

            script = f'''#!/bin/bash
cd "{src}"
echo "=== Mangopret installer ==="
echo "This will install zapret v{ZAPRET_VERSION} to {self.zapret_dir}"
echo ""

# Check root
if [ "$(id -u)" -ne 0 ]; then
    echo "Requesting root access..."
    sudo bash "{installer}" "{src}" "{self.zapret_dir}"
else
    bash "{installer}" "{src}" "{self.zapret_dir}"
fi

echo ""
echo "=== Installation finished ==="
echo "Press Enter to close..."
read
'''
            script_path = tmpdir / "install_mangopret.sh"
            script_path.write_text(script)
            script_path.chmod(0o755)

            term = self._find_terminal()
            if not term:
                if callback:
                    callback("No terminal emulator found. Install x-terminal-emulator.")
                return False

            subprocess.Popen([term, "-e", f"bash {script_path}"])

            if callback:
                callback("Opened installer in terminal. Follow the prompts there.")
            return True

        except Exception as e:
            if callback:
                callback(f"Error: {e}")
            return False

    def _install_zapret_windows(self, callback=None) -> bool:
        try:
            tmpdir = Path(tempfile.mkdtemp(prefix="mangopret_"))

            if callback:
                callback(f"Downloading zapret-win-bundle ...")

            releases_url = "https://api.github.com/repos/bol-van/zapret/releases/latest"
            req = urllib.request.Request(releases_url, headers={"User-Agent": "Mangopret"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            asset_url = None
            for asset in data.get("assets", []):
                name = asset["name"].lower()
                if name.endswith(".zip") and ("win" in name or "bundle" in name):
                    asset_url = asset["browser_download_url"]
                    break

            if not asset_url:
                if callback:
                    callback("No suitable Windows release asset found")
                return False

            if callback:
                callback(f"Downloading {asset_url} ...")

            archive = tmpdir / "zapret.zip"
            urllib.request.urlretrieve(asset_url, archive)

            if callback:
                callback("Extracting ...")

            with zipfile.ZipFile(archive, "r") as zf:
                zf.extractall(tmpdir)

            for d in tmpdir.iterdir():
                if d.is_dir() and "bin" in [x.name for x in d.iterdir()]:
                    shutil.copytree(d / "bin", self.bin_dir, dirs_exist_ok=True)
                    break

            if callback:
                callback("Done!")
            return True

        except Exception as e:
            if callback:
                callback(f"Error: {e}")
            return False
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------ start / stop
    def get_winws_args(self, wf_tcp, wf_udp, game_filter_tcp, game_filter_udp) -> list:
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

    def get_nfqueue_args(self, queue_num="200") -> list:
        return ["--queue-num", queue_num]

    def build_iptables_rules(self, wf_tcp, wf_udp, queue_num="200") -> list:
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

    def start_service(self, strategy_name: str, args: list) -> Optional[subprocess.Popen]:
        cmd = [str(self.binary)] + args
        if self.is_windows:
            return subprocess.Popen(
                cmd,
                creationflags=_WIN_CREATE_NO_WINDOW | _WIN_BELOW_NORMAL_PRIORITY,
                cwd=str(self.bin_dir),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        else:
            return subprocess.Popen(
                cmd,
                cwd=str(self.bin_dir),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
                creationflags=_WIN_CREATE_NO_WINDOW,
            )
        else:
            subprocess.run(["pkill", "-f", "nfqws"], capture_output=True)
            self._cleanup_iptables()

    def _cleanup_iptables(self):
        if not self.is_linux:
            return
        try:
            for chain in ("OUTPUT", "FORWARD"):
                result = subprocess.run(
                    ["iptables", "-t", "mangle", "-L", chain, "--line-numbers"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in reversed(result.stdout.splitlines()):
                    parts = line.split()
                    if len(parts) >= 1 and parts[0].isdigit():
                        subprocess.run(
                            ["iptables", "-t", "mangle", "-D", chain, parts[0]],
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
                    creationflags=_WIN_CREATE_NO_WINDOW,
                )
                return name.lower() in r.stdout.lower()
            else:
                r = subprocess.run(["pgrep", "-f", name], capture_output=True, timeout=5)
                return r.returncode == 0
        except Exception:
            return False

    # ------------------------------------------------------------------ service
    def get_service_status(self) -> str:
        if self.is_windows:
            try:
                r = subprocess.run(
                    ["sc", "query", "zapret"],
                    capture_output=True, text=True, timeout=10,
                    creationflags=_WIN_CREATE_NO_WINDOW,
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
                    ["systemctl", "is-active", "mangopret"],
                    capture_output=True, text=True, timeout=5,
                )
                if r.stdout.strip() == "active":
                    return "running"
                elif r.stdout.strip() == "inactive":
                    return "stopped"
                elif r.stdout.strip() == "failed":
                    return "failed"
            except Exception:
                pass
            return "not_installed"

    def is_service_enabled(self) -> bool:
        if self.is_linux:
            try:
                r = subprocess.run(
                    ["systemctl", "is-enabled", "mangopret"],
                    capture_output=True, text=True, timeout=5,
                )
                return r.stdout.strip() == "enabled"
            except Exception:
                pass
        return False

    def create_systemd_service(self, strategy_cmd: list, strategy_name: str = "") -> bool:
        if not self.is_linux:
            return False
        try:
            unit_dir = Path("/etc/systemd/system")
            unit_file = unit_dir / "mangopret.service"
            exec_start = " ".join(str(x) for x in strategy_cmd)
            unit_content = f"""[Unit]
Description=Mangopret DPI Bypass - {strategy_name}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={exec_start}
WorkingDirectory={self.zapret_dir}
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
            print(f"[mangopret] Writing service to {unit_file}")
            print(f"[mangopret] ExecStart: {exec_start}")
            unit_file.write_text(unit_content, encoding="utf-8")
            print(f"[mangopret] Service file written, reloading daemon...")
            r = subprocess.run(["systemctl", "daemon-reload"], capture_output=True, text=True, timeout=10)
            print(f"[mangopret] daemon-reload: rc={r.returncode} stderr={r.stderr}")
            return True
        except Exception as e:
            print(f"[mangopret] Failed to create systemd service: {e}")
            import traceback
            traceback.print_exc()
            return False

    def start_systemd_service(self) -> tuple:
        try:
            r = subprocess.run(
                ["systemctl", "start", "mangopret"],
                capture_output=True, text=True, timeout=10,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as e:
            return (False, str(e))

    def stop_systemd_service(self) -> tuple:
        try:
            r = subprocess.run(
                ["systemctl", "stop", "mangopret"],
                capture_output=True, text=True, timeout=10,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as e:
            return (False, str(e))

    def enable_systemd_service(self) -> tuple:
        try:
            r = subprocess.run(
                ["systemctl", "enable", "mangopret"],
                capture_output=True, text=True, timeout=10,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as e:
            return (False, str(e))

    def disable_systemd_service(self) -> tuple:
        try:
            r = subprocess.run(
                ["systemctl", "disable", "mangopret"],
                capture_output=True, text=True, timeout=10,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as e:
            return (False, str(e))

    def remove_systemd_service(self) -> tuple:
        try:
            subprocess.run(["systemctl", "stop", "mangopret"], capture_output=True, timeout=10)
            subprocess.run(["systemctl", "disable", "mangopret"], capture_output=True, timeout=10)
            unit_file = Path("/etc/systemd/system/mangopret.service")
            if unit_file.exists():
                unit_file.unlink()
            subprocess.run(["systemctl", "daemon-reload"], capture_output=True, timeout=10)
            return (True, "")
        except Exception as e:
            return (False, str(e))

    def start_windows_service(self) -> tuple:
        if not self.is_windows:
            return (False, "Not Windows")
        try:
            r = subprocess.run(
                ["sc", "start", "zapret"],
                capture_output=True, text=True, timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as e:
            return (False, str(e))

    def stop_windows_service(self) -> tuple:
        if not self.is_windows:
            return (False, "Not Windows")
        try:
            r = subprocess.run(
                ["sc", "stop", "zapret"],
                capture_output=True, text=True, timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as e:
            return (False, str(e))

    # ------------------------------------------------------------------ iptables
    def install_iptables_rules(self, wf_tcp, wf_udp, queue_num="200") -> list:
        if not self.is_linux:
            return []
        rules = self.build_iptables_rules(wf_tcp, wf_udp, queue_num)
        results = []
        for rule in rules:
            try:
                r = subprocess.run(rule.split(), capture_output=True, text=True, timeout=10)
                results.append((rule, r.returncode == 0, r.stderr.strip() if r.stderr else ""))
            except Exception as e:
                results.append((rule, False, str(e)))
        return results

    def remove_iptables_rules(self) -> bool:
        if not self.is_linux:
            return False
        self._cleanup_iptables()
        return True

    def get_journal_logs(self, lines=50) -> str:
        if not self.is_linux:
            return ""
        try:
            r = subprocess.run(
                ["journalctl", "-u", "mangopret", "-n", str(lines), "--no-pager"],
                capture_output=True, text=True, timeout=10,
            )
            return r.stdout
        except Exception:
            return ""

    def create_desktop_entry(self) -> tuple:
        if not self.is_linux:
            return (False, "Not Linux")
        try:
            desktop_dir = Path.home() / ".local" / "share" / "applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)
            dest = desktop_dir / "mangopret.desktop"
            src = self.base_dir / "mangopret.desktop"
            if src.exists():
                shutil.copy2(str(src), str(dest))
                dest.chmod(0o644)
                return (True, str(dest))
            return (False, "mangopret.desktop not found in project")
        except Exception as e:
            return (False, str(e))

    def remove_desktop_entry(self) -> tuple:
        if not self.is_linux:
            return (False, "Not Linux")
        try:
            dest = Path.home() / ".local" / "share" / "applications" / "mangopret.desktop"
            if dest.exists():
                dest.unlink()
                return (True, "")
            return (False, "Not installed")
        except Exception as e:
            return (False, str(e))

    def is_desktop_entry_installed(self) -> bool:
        if not self.is_linux:
            return False
        return (Path.home() / ".local" / "share" / "applications" / "mangopret.desktop").exists()
