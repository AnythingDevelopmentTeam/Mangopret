import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from core.log import get_logger

logger = get_logger(__name__)

ZAPRET_VERSION = "1.0.3"
ZAPRET_URL = (
    f"https://github.com/bol-van/zapret2/releases/download/"
    f"v{ZAPRET_VERSION}/zapret2-v{ZAPRET_VERSION}.tar.gz"
)
ZAPRET_DIR = Path("/opt/zapret")

_WIN_CREATE_NO_WINDOW = 0x08000000
_WIN_BELOW_NORMAL_PRIORITY = 0x00008000


class PlatformInfo:
    is_windows: bool = sys.platform == "win32"
    is_linux: bool = sys.platform == "linux"

    IS_ROOT: bool = sys.platform != "win32" and os.geteuid() == 0

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.bin_dir = self.base_dir / "bin"
        self.lists_dir = self.base_dir / "lists"
        self.utils_dir = self.base_dir / "utils"
        self.strategies_dir = self.base_dir / "strategies"
        self.config_dir = self._get_config_dir()
        self.zapret_dir = ZAPRET_DIR
        self._binary_name = "nfqws2" if not self.is_windows else "winws2.exe"

        if self.is_windows:
            self.binary = self.bin_dir / self._binary_name
        else:
            self._resolve_binary()

    @property
    def _service_unit_name(self) -> str:
        return "mangopret2.service"

    def _resolve_binary(self) -> None:
        candidates = [
            self.zapret_dir / "nfq2" / "nfqws2",
            self.zapret_dir / "bin" / "nfqws2",
            self.zapret_dir / "binaries" / "linux-x86_64" / "nfqws2",
            self.bin_dir / "nfqws2",
        ]
        for c in candidates:
            if c.exists():
                self.binary = c
                return
        self.binary = candidates[0]

    def _get_config_dir(self) -> Path:
        if self.is_windows:
            base = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        else:
            base = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        return Path(base) / "mangopret"

    def ensure_dirs(self) -> None:
        for d in [self.config_dir, self.bin_dir, self.lists_dir, self.utils_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def is_binary_present(self) -> bool:
        return self.binary.exists()

    def is_zapret_installed(self) -> bool:
        if self.is_windows:
            return True
        return (self.zapret_dir / "install_easy.sh").exists()

    def ensure_zapret(self, callback: Callable[[str], None] | None = None) -> bool:
        if self.is_zapret_installed():
            return True
        return self.install_zapret(callback=callback)

    # ------------------------------------------------------------------ install

    def install_zapret(self, callback: Callable[[str], None] | None = None) -> bool:
        if self.is_windows:
            if callback:
                callback("Zapret is already bundled — nothing to install.")
            return True
        return self._install_zapret_linux(callback)

    @staticmethod
    def _is_atomic_system() -> bool:
        try:
            if shutil.which("rpm-ostree"):
                return True
            if Path("/run/ostree-booted").exists():
                return True
        except Exception:
            pass
        return False

    def _install_zapret_linux(
        self, callback: Callable[[str], None] | None = None
    ) -> bool:
        return self._install_zapret_common(
            url=ZAPRET_URL,
            version_label=f"zapret v{ZAPRET_VERSION}",
            archive_name="zapret.tar.gz",
            dir_prefix="zapret2",
            callback=callback,
        )

    def _install_zapret_common(
        self,
        url: str,
        version_label: str,
        archive_name: str,
        dir_prefix: str,
        callback: Callable[[str], None] | None = None,
    ) -> bool:
        tmpdir: Path | None = None
        try:
            base = Path.home() / ".local" / "tmp"
            base.mkdir(parents=True, exist_ok=True)
            tmpdir = Path(tempfile.mkdtemp(dir=str(base), prefix="mangopret_"))

            if callback:
                callback(f"Downloading {version_label} ...")
            archive = tmpdir / archive_name
            urllib.request.urlretrieve(url, archive)

            if callback:
                callback("Extracting ...")
            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(tmpdir)

            src: Path | None = None
            for d in tmpdir.iterdir():
                if d.is_dir() and d.name.startswith(dir_prefix):
                    src = d
                    break
            src = src or tmpdir

            target = self.zapret_dir
            if callback:
                callback(f"Installing to {target} ...")

            if target.exists() and any(target.iterdir()):
                if callback:
                    callback(f"Cleaning existing {target} ...")
                shutil.rmtree(target)

            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(str(src), str(target), symlinks=True)

            (target / "tmp").mkdir(exist_ok=True)

            ipset_dir = target / "ipset"
            ipset_dir.mkdir(parents=True, exist_ok=True)

            exclude_file = ipset_dir / "zapret-hosts-user-exclude.txt"
            if not exclude_file.exists():
                default_exclude = ipset_dir / "zapret-hosts-user-exclude.txt.default"
                if default_exclude.exists():
                    shutil.copy2(default_exclude, exclude_file)
                else:
                    exclude_file.touch()

            user_file = ipset_dir / "zapret-hosts-user.txt"
            if not user_file.exists():
                user_file.write_text("nonexistent.domain\n")

            ipban_file = ipset_dir / "zapret-hosts-user-ipban.txt"
            if not ipban_file.exists():
                ipban_file.touch()

            if self._is_atomic_system():
                if callback:
                    callback(
                        "Atomic system detected — install_bin_atomic.sh not found, creating symlinks directly"
                    )
            else:
                if callback:
                    callback("Detecting architecture and linking binaries ...")
                subprocess.run(
                    ["bash", str(target / "install_bin.sh")],
                    cwd=str(target),
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )

            if callback:
                callback("Setting permissions ...")
            for d in target.rglob("*"):
                if d.is_dir():
                    d.chmod(0o755)
                elif d.is_file():
                    d.chmod(0o644)
            subprocess.run(
                ["chown", "-R", "root:root", str(target)],
                capture_output=True,
                timeout=30,
                check=False,
            )
            for pattern in ("ip2net", "nfqws2", "tpws", "mdig"):
                for f in (target / "binaries").rglob(pattern):
                    f.chmod(0o755)
            for script in (
                "install_bin.sh",
                "install_easy.sh",
                "install_prereq.sh",
                "blockcheck.sh",
                "blockcheck2.sh",
                "uninstall_easy.sh",
            ):
                p = target / script
                if p.exists():
                    p.chmod(0o755)

            if callback:
                callback("Installation complete!")
            return True

        except subprocess.TimeoutExpired:
            if callback:
                callback("Error: installation timed out after 10 minutes")
            return False
        except Exception as exc:
            if callback:
                callback(f"Error: {exc}")
            logger.error("Zapret Linux install failed: %s", exc)
            return False
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------ process

    def start_process(self, args: list) -> subprocess.Popen | None:
        cmd = [str(self.binary)] + args
        kwargs: dict[str, Any] = {
            "cwd": str(self.bin_dir),
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
        }
        if self.is_windows:
            kwargs["creationflags"] = _WIN_CREATE_NO_WINDOW | _WIN_BELOW_NORMAL_PRIORITY
        try:
            return subprocess.Popen(cmd, **kwargs)
        except Exception as exc:
            logger.error("Failed to start process: %s", exc)
            return None

    def stop_process(self, proc: subprocess.Popen | None) -> None:
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        except Exception as exc:
            logger.debug("stop_process exception: %s", exc)

    def is_process_running(self, name: str | None = None) -> bool:
        if name is None:
            name = "winws2.exe" if self.is_windows else "nfqws2"
        try:
            if self.is_windows:
                r = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {name}"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=5,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                    check=False,
                )
                return name.lower() in r.stdout.lower()
            else:
                r = subprocess.run(
                    ["pgrep", "-f", name], capture_output=True, timeout=5, check=False
                )
                return r.returncode == 0
        except Exception as exc:
            logger.warning("Failed to check running process: %s", exc)
            return False

    def kill_all(self) -> None:
        if self.is_windows:
            subprocess.run(
                ["taskkill", "/IM", "winws2.exe", "/F"],
                capture_output=True,
                creationflags=_WIN_CREATE_NO_WINDOW,
                check=False,
            )
        else:
            subprocess.run(["pkill", "-f", "nfqws2"], capture_output=True, check=False)

    # ------------------------------------------------------------------ service

    def get_service_status(self) -> str:
        if self.is_windows:
            return self._get_windows_service_status()
        return self._get_systemd_service_status()

    def _get_windows_service_status(self) -> str:
        try:
            r = subprocess.run(
                ["sc", "query", "zapret"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
                check=False,
            )
            if "RUNNING" in r.stdout:
                return "running"
            elif "STOPPED" in r.stdout:
                return "stopped"
        except Exception as exc:
            logger.debug("Windows service status check failed: %s", exc)
        return "not_installed"

    def _get_systemd_service_status(self) -> str:
        unit_file = Path(f"/etc/systemd/system/{self._service_unit_name}")
        if not unit_file.exists():
            return "not_installed"
        svc_name = self._service_unit_name.replace(".service", "")
        try:
            r = subprocess.run(
                ["systemctl", "is-active", svc_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
            state = r.stdout.strip()
            if state == "active":
                return "running"
            elif state == "activating":
                return "starting"
            elif state == "failed":
                return "failed"
            elif state == "inactive":
                return "stopped"
        except Exception as exc:
            logger.debug("systemd status check failed: %s", exc)
        return "not_installed"

    def is_service_enabled(self) -> bool:
        if not self.is_linux:
            return False
        svc_name = self._service_unit_name.replace(".service", "")
        try:
            r = subprocess.run(
                ["systemctl", "is-enabled", svc_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
            return r.stdout.strip() == "enabled"
        except Exception as exc:
            logger.debug("systemd enabled check failed: %s", exc)
            return False

    def create_systemd_service(self, strategy, strategy_name: str = "") -> bool:
        if not self.is_linux:
            return False
        return self._create_systemd_service(strategy, strategy_name)

    def _create_systemd_service(self, strategy, strategy_name: str) -> bool:
        try:
            qnum = self._get_config_value("nfqueue_num", "200")
            auto_hostlist = self._get_config_value("auto_hostlist", "False") == "True"
            ipcache = self._get_config_value("ipcache", "False") == "True"

            cmd_args = strategy.build_command(
                str(self.binary),
                str(self.bin_dir),
                str(self.lists_dir),
                False,
                auto_hostlist=auto_hostlist,
                ipcache=ipcache,
            )
            cmd_str = " ".join(cmd_args)

            wf_tcp = strategy.wf_tcp
            wf_udp = strategy.wf_udp

            wrapper = self.zapret_dir / "mangopret-wrapper.sh"
            wrapper_content = (
                "#!/bin/bash\n"
                "set -e\n"
                f"cd {self.zapret_dir}\n"
                "cleanup() {\n"
                "  if command -v nft &>/dev/null; then\n"
                "    nft delete table inet ztest 2>/dev/null || true\n"
                "  elif command -v iptables &>/dev/null; then\n"
                f"    while iptables -t mangle -D OUTPUT -j NFQUEUE --queue-num {qnum} 2>/dev/null; do :; done\n"
                "  fi\n"
                "}\n"
                "trap cleanup EXIT TERM INT\n"
                "# install NFQUEUE rules for nfqws2\n"
                f'for port in $(echo "{wf_tcp}" | tr "," " "); do\n'
                "  if command -v nft &>/dev/null; then\n"
                f"    nft add rule inet ztest output tcp dport $port queue num {qnum} 2>/dev/null || \\\n"
                f"      nft add table inet ztest 2>/dev/null; \\\n"
                f"      nft add chain inet ztest output '{{ type filter hook output priority 0; }}' 2>/dev/null; \\\n"
                f"      nft add rule inet ztest output tcp dport $port queue num {qnum}\n"
                "  elif command -v iptables &>/dev/null; then\n"
                f"    iptables -t mangle -A OUTPUT -p tcp --dport $port -j NFQUEUE --queue-num {qnum} || true\n"
                "  fi\n"
                "done\n"
                f'for port in $(echo "{wf_udp}" | tr "," " "); do\n'
                "  port=$(echo $port | cut -d'-' -f1)\n"
                "  if command -v nft &>/dev/null; then\n"
                f"    nft add rule inet ztest output udp dport $port queue num {qnum} 2>/dev/null || true\n"
                "  elif command -v iptables &>/dev/null; then\n"
                f"    iptables -t mangle -A OUTPUT -p udp --dport $port -j NFQUEUE --queue-num {qnum} || true\n"
                "  fi\n"
                "done\n"
                "# start nfqws2\n"
                f"exec {cmd_str}\n"
            )
            wrapper.write_text(wrapper_content)
            wrapper.chmod(0o755)

            unit = (
                "[Unit]\n"
                "Description=zapret DPI bypass (mangopret-managed)\n"
                "After=network.target\n"
                "\n"
                "[Service]\n"
                "Type=simple\n"
                f"ExecStart={wrapper}\n"
                "Restart=on-failure\n"
                "\n"
                "[Install]\n"
                "WantedBy=multi-user.target\n"
            )
            unit_file = Path(f"/etc/systemd/system/{self._service_unit_name}")
            unit_file.write_text(unit, encoding="utf-8")

            subprocess.run(
                ["systemctl", "daemon-reload"],
                capture_output=True,
                timeout=10,
                check=False,
            )
            return True
        except Exception as exc:
            logger.error("Failed to create systemd service: %s", exc)
            return False

    def _get_config_value(self, key: str, default: str) -> str:
        try:
            config_file = self.config_dir / "config.json"
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = json.load(f)
                return config.get(key, default)
        except Exception as exc:
            logger.debug("Failed to read config value %s: %s", key, exc)
        return default

    def _systemd_cmd(self, action: str, service_name: str = "") -> tuple[bool, str]:
        if not service_name:
            service_name = self._service_unit_name.replace(".service", "")
        try:
            r = subprocess.run(
                ["systemctl", action, service_name],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as exc:
            return (False, str(exc))

    def start_systemd_service(self) -> tuple[bool, str]:
        return self._systemd_cmd("start")

    def stop_systemd_service(self) -> tuple[bool, str]:
        return self._systemd_cmd("stop")

    def enable_systemd_service(self) -> tuple[bool, str]:
        return self._systemd_cmd("enable")

    def disable_systemd_service(self) -> tuple[bool, str]:
        return self._systemd_cmd("disable")

    def remove_systemd_service(self) -> tuple[bool, str]:
        try:
            for svc in ("zapret", "mangopret", "mangopret2"):
                self._systemd_cmd("stop", service_name=svc)
                self._systemd_cmd("disable", service_name=svc)
            for name in ("zapret.service", "mangopret.service", "mangopret2.service"):
                unit_file = Path("/etc/systemd/system") / name
                if unit_file.exists():
                    unit_file.unlink()
            subprocess.run(
                ["systemctl", "daemon-reload"],
                capture_output=True,
                timeout=10,
                check=False,
            )
            return (True, "")
        except Exception as exc:
            return (False, str(exc))

    def _windows_svc_cmd(self, action: str) -> tuple[bool, str]:
        if not self.is_windows:
            return (False, "Not Windows")
        try:
            r = subprocess.run(
                ["sc", action, "zapret"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
                check=False,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as exc:
            return (False, str(exc))

    def start_windows_service(self) -> tuple[bool, str]:
        return self._windows_svc_cmd("start")

    def stop_windows_service(self) -> tuple[bool, str]:
        return self._windows_svc_cmd("stop")

    def service_start(self) -> tuple[bool, str]:
        if self.is_windows:
            return self.start_windows_service()
        return self.start_systemd_service()

    def service_stop(self) -> tuple[bool, str]:
        if self.is_windows:
            return self.stop_windows_service()
        return self.stop_systemd_service()

    def service_remove(self) -> tuple[bool, str]:
        if self.is_windows:
            return self._remove_windows_service()
        return self.remove_systemd_service()

    def _remove_windows_service(self) -> tuple[bool, str]:
        if not self.is_windows:
            return (False, "Not Windows")
        try:
            for svc in ["zapret", "WinDivert"]:
                subprocess.run(
                    ["net", "stop", svc],
                    capture_output=True,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                    check=False,
                )
                subprocess.run(
                    ["sc", "delete", svc],
                    capture_output=True,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                    check=False,
                )
            return (True, "")
        except Exception as exc:
            return (False, str(exc))

    def validate_binary_dry_run(self, args: list[str]) -> tuple[bool, str]:
        """Run nfqws2 --dry-run to validate config before starting."""
        if not self.binary or not self.binary.exists():
            return (False, f"Binary not found: {self.binary}")
        try:
            dry_args = [str(self.binary), "--dry-run"] + args[1:]
            r = subprocess.run(
                dry_args,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if r.returncode == 0:
                return (True, r.stdout.strip())
            return (False, r.stderr.strip() or r.stdout.strip())
        except subprocess.TimeoutExpired:
            return (False, "dry-run timed out")
        except Exception as exc:
            return (False, str(exc))

    def service_install(
        self, strategy=None, strategy_name: str = ""
    ) -> tuple[bool, str]:
        if self.is_windows:
            return self._install_windows_service(strategy)
        if strategy:
            ok = self.create_systemd_service(strategy, strategy_name)
            return (ok, "" if ok else "Failed to create service")
        return (False, "No strategy provided")

    def _install_windows_service(self, strategy=None) -> tuple[bool, str]:
        if not self.is_windows:
            return (False, "Not Windows")
        try:
            bin_path = str(self.binary)
            if strategy:
                args = strategy.build_command(
                    str(self.binary),
                    str(self.bin_dir),
                    str(self.lists_dir),
                    True,
                )
                cmd_args = " ".join(str(x) for x in args[1:])
                sc_cmd = f'"{bin_path}" {cmd_args}'
            else:
                sc_cmd = f'"{bin_path}"'

            r = subprocess.run(
                [
                    "sc",
                    "create",
                    "zapret",
                    "binPath=",
                    sc_cmd,
                    "DisplayName=",
                    "zapret",
                    "start=",
                    "auto",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
                check=False,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as exc:
            return (False, str(exc))

    # ------------------------------------------------------------------ journal

    def get_journal_logs(self, lines: int = 50) -> str:
        if not self.is_linux:
            return ""
        try:
            r = subprocess.run(
                [
                    "journalctl",
                    "-u",
                    self._service_unit_name,
                    "-n",
                    str(lines),
                    "--no-pager",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
            return r.stdout
        except Exception as exc:
            logger.warning("Failed to get journal logs: %s", exc)
            return ""

    # ------------------------------------------------------------------ startup (autostart on login)

    def is_startup_enabled(self) -> bool:
        if self.is_windows:
            try:
                r = subprocess.run(
                    ["schtasks", "/query", "/tn", "Mangopret"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=10,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                    check=False,
                )
                return r.returncode == 0
            except Exception as exc:
                logger.debug("Startup check failed: %s", exc)
                return False
        else:
            return (
                Path.home() / ".config" / "autostart" / "mangopret.desktop"
            ).exists()

    def enable_startup(self) -> tuple[bool, str]:
        if self.is_windows:
            return self._enable_startup_windows()
        return self._enable_startup_linux()

    def _enable_startup_linux(self) -> tuple[bool, str]:
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            dest = autostart_dir / "mangopret.desktop"
            content = (
                "[Desktop Entry]\n"
                "Name=Mangopret\n"
                "Comment=Cross-platform DPI bypass manager\n"
                f"Exec=bash -c 'cd \"{self.base_dir}\" && ./run_gui.sh --minimized'\n"
                "Icon=mangopret\n"
                "Terminal=false\n"
                "Type=Application\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
            dest.write_text(content, encoding="utf-8")
            dest.chmod(0o644)
            return (True, "")
        except Exception as exc:
            return (False, str(exc))

    def _enable_startup_windows(self) -> tuple[bool, str]:
        try:
            gui_bat = self.base_dir / "run_gui.bat"
            if not gui_bat.exists():
                return (False, "run_gui.bat not found")
            cmd = f'cmd.exe /c "cd /d \\"{self.base_dir}\\" && run_gui.bat --minimized"'
            r = subprocess.run(
                [
                    "schtasks",
                    "/create",
                    "/tn",
                    "Mangopret",
                    "/tr",
                    cmd,
                    "/sc",
                    "onlogon",
                    "/rl",
                    "highest",
                    "/f",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
                creationflags=_WIN_CREATE_NO_WINDOW,
                check=False,
            )
            if r.returncode == 0:
                return (True, "")
            return (False, r.stderr.strip() or r.stdout.strip())
        except Exception as exc:
            return (False, str(exc))

    def disable_startup(self) -> tuple[bool, str]:
        if self.is_windows:
            return self._disable_startup_windows()
        return self._disable_startup_linux()

    def _disable_startup_linux(self) -> tuple[bool, str]:
        try:
            dest = Path.home() / ".config" / "autostart" / "mangopret.desktop"
            if dest.exists():
                dest.unlink()
                return (True, "")
            return (False, "Not installed")
        except Exception as exc:
            return (False, str(exc))

    def _disable_startup_windows(self) -> tuple[bool, str]:
        try:
            r = subprocess.run(
                ["schtasks", "/delete", "/tn", "Mangopret", "/f"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
                check=False,
            )
            if r.returncode == 0:
                return (True, "")
            return (False, r.stderr.strip() or r.stdout.strip())
        except Exception as exc:
            return (False, str(exc))
