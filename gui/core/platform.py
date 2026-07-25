import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional, Tuple, List
from core.log import get_logger

logger = get_logger(__name__)

ZAPRET_VERSION = "72.13"
ZAPRET_URL = (
    f"https://github.com/bol-van/zapret/releases/download/"
    f"v{ZAPRET_VERSION}/zapret-v{ZAPRET_VERSION}.tar.gz"
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
        self.strategies_dir = self.base_dir / "gui" / "strategies"
        self.config_dir = self._get_config_dir()
        self.zapret_dir = ZAPRET_DIR

        if self.is_windows:
            self.binary = self.bin_dir / "winws.exe"
        else:
            self._resolve_binary()

    def _resolve_binary(self) -> None:
        candidates = [
            self.zapret_dir / "nfq" / "nfqws",
            self.zapret_dir / "bin" / "nfqws",
            self.zapret_dir / "binaries" / "linux-x86_64" / "nfqws",
            self.bin_dir / "nfqws",
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
        return (self.zapret_dir / "install_easy.sh").exists() or (
            self.zapret_dir / "config"
        ).exists()

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

    def _install_zapret_linux(self, callback: Callable[[str], None] | None = None) -> bool:
        tmpdir: Path | None = None
        try:
            base = Path.home() / ".local" / "tmp"
            base.mkdir(parents=True, exist_ok=True)
            tmpdir = Path(tempfile.mkdtemp(dir=str(base), prefix="mangopret_"))

            if callback:
                callback(f"Downloading zapret v{ZAPRET_VERSION} ...")
            archive = tmpdir / "zapret.tar.gz"
            urllib.request.urlretrieve(ZAPRET_URL, archive)

            if callback:
                callback("Extracting ...")
            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(tmpdir)

            src: Path | None = None
            for d in tmpdir.iterdir():
                if d.is_dir() and d.name.startswith("zapret"):
                    src = d
                    break
            src = src or tmpdir

            if callback:
                callback(f"Installing to {self.zapret_dir} ...")

            installer = Path(__file__).parent.parent.parent / "silent_install.sh"
            if not installer.exists():
                if callback:
                    callback(f"Error: installer not found at {installer}")
                return False

            proc = subprocess.run(
                ["bash", str(installer), str(src), str(self.zapret_dir)],
                capture_output=True, text=True, timeout=600,
            )
            for line in proc.stdout.splitlines():
                if callback:
                    callback(line)
            if proc.returncode != 0:
                if callback:
                    callback(f"Installer failed (exit code {proc.returncode})")
                    if proc.stderr:
                        for line in proc.stderr.splitlines()[-5:]:
                            callback(line)
                return False

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

    def start_process(self, args: list) -> Optional[subprocess.Popen]:
        cmd = [str(self.binary)] + args
        kwargs: dict[str, Any] = dict(
            cwd=str(self.bin_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if self.is_windows:
            kwargs["creationflags"] = _WIN_CREATE_NO_WINDOW | _WIN_BELOW_NORMAL_PRIORITY
        try:
            return subprocess.Popen(cmd, **kwargs)
        except Exception as exc:
            logger.error("Failed to start process: %s", exc)
            return None

    def stop_process(self, proc: Optional[subprocess.Popen]) -> None:
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
        except Exception as exc:
            logger.warning("Failed to check running process: %s", exc)
            return False

    def kill_all(self) -> None:
        if self.is_windows:
            subprocess.run(
                ["taskkill", "/IM", "winws.exe", "/F"],
                capture_output=True,
                creationflags=_WIN_CREATE_NO_WINDOW,
            )
        else:
            subprocess.run(["pkill", "-f", "nfqws"], capture_output=True)

    # ------------------------------------------------------------------ service

    def get_service_status(self) -> str:
        if self.is_windows:
            return self._get_windows_service_status()
        return self._get_systemd_service_status()

    def _get_windows_service_status(self) -> str:
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
        except Exception as exc:
            logger.debug("Windows service status check failed: %s", exc)
        return "not_installed"

    def _get_systemd_service_status(self) -> str:
        unit_file = Path("/etc/systemd/system/zapret.service")
        if not unit_file.exists():
            return "not_installed"
        try:
            r = subprocess.run(
                ["systemctl", "is-active", "zapret"],
                capture_output=True, text=True, timeout=5,
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
        try:
            r = subprocess.run(
                ["systemctl", "is-enabled", "zapret"],
                capture_output=True, text=True, timeout=5,
            )
            return r.stdout.strip() == "enabled"
        except Exception as exc:
            logger.debug("systemd enabled check failed: %s", exc)
            return False

    def create_systemd_service(self, strategy, strategy_name: str = "") -> bool:
        if not self.is_linux:
            return False
        try:
            nfqws_opt = self._build_nfqws_opt(strategy)
            wf_tcp = strategy.wf_tcp
            wf_udp = strategy.wf_udp
            queue_num = self._get_config_value("nfqueue_num", "200")

            config_path = self.zapret_dir / "config"
            existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""

            def _replace_or_append(lines: list[str], key: str, value: str) -> None:
                found = False
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} "):
                        lines[i] = f"{key}={value}\n"
                        found = True
                        break
                if not found:
                    lines.append(f"{key}={value}\n")

            if existing:
                lines = existing.splitlines(keepends=True)
            else:
                lines = [
                    "# Mangopret-managed zapret config\n",
                    f"SET_MAXELEM=522288\n",
                    f'IPSET_OPT="hashsize 262144 maxelem $SET_MAXELEM"\n',
                    f"DESYNC_MARK=0x40000000\n",
                    f"DESYNC_MARK_POSTNAT=0x20000000\n",
                    f"DISABLE_IPV6=1\n",
                    f"INIT_APPLY_FW=1\n",
                    f"FWTYPE=nftables\n",
                ]

            _replace_or_append(lines, "NFQWS_ENABLE", "1")
            _replace_or_append(lines, "NFQWS_PORTS_TCP", wf_tcp)
            _replace_or_append(lines, "NFQWS_PORTS_UDP", wf_udp)
            _replace_or_append(lines, "MODE_FILTER", "none")
            _replace_or_append(lines, "TPWS_ENABLE", "0")
            _replace_or_append(lines, "TPWS_SOCKS_ENABLE", "0")
            _replace_or_append(lines, "FILTER_TTL_EXPIRED_ICMP", "1")

            nfqws_opt_escaped = f'"\n{nfqws_opt}\n"'
            nfqws_opt_line = f"NFQWS_OPT={nfqws_opt_escaped}"
            in_nfqws_opt = False
            new_lines: list[str] = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("NFQWS_OPT=") or stripped.startswith("NFQWS_OPT "):
                    in_nfqws_opt = True
                    new_lines.append(nfqws_opt_line + "\n")
                    continue
                if in_nfqws_opt:
                    if stripped.startswith('"') and not stripped.startswith("NFQWS"):
                        in_nfqws_opt = False
                        continue
                    if stripped.endswith('"'):
                        in_nfqws_opt = False
                        continue
                    continue
                new_lines.append(line)

            if not any(l.strip().startswith("NFQWS_OPT=") for l in new_lines):
                new_lines.append(nfqws_opt_line + "\n")

            config_path.write_text("".join(new_lines), encoding="utf-8")
            logger.info("Wrote config to %s", config_path)

            self._sync_ipset_files(strategy)
            self._install_zapret_service_unit(strategy_name)
            return True
        except Exception as exc:
            logger.error("Failed to create systemd service: %s", exc)
            return False

    def _build_nfqws_opt(self, strategy) -> str:
        parts: list[str] = []
        for rule in strategy.rules:
            args = rule.to_args()
            resolved: list[str] = []
            skip = False
            for arg in args:
                if arg.startswith("--"):
                    keyval = arg.split("=", 1)
                    if len(keyval) == 2:
                        val = self._resolve_zapret_path(keyval[1])
                        if keyval[0] in ("--filter-tcp", "--filter-udp") and not val.strip():
                            skip = True
                            break
                        resolved.append(f"{keyval[0]}={val}")
                    else:
                        resolved.append(keyval[0])
                else:
                    resolved.append(self._resolve_zapret_path(arg))
            if not skip:
                parts.append(" ".join(resolved))
        return " --new\n".join(parts)

    @staticmethod
    def _resolve_zapret_path(value: str) -> str:
        value = value.replace("{bin}", str(ZAPRET_DIR / "files" / "fake"))
        value = value.replace("{lists}", str(ZAPRET_DIR / "ipset"))
        value = value.replace("{game_filter_tcp}", "")
        value = value.replace("{game_filter_udp}", "")
        return value

    def _sync_ipset_files(self, strategy) -> None:
        zapret_ipset = self.zapret_dir / "ipset"
        zapret_ipset.mkdir(parents=True, exist_ok=True)

        copied_ipset: set[str] = set()
        copied_bin: set[str] = set()

        for rule in strategy.rules:
            for key, vals in rule.params.items():
                if vals is None:
                    continue
                if not isinstance(vals, list):
                    vals = [vals]
                for val in vals:
                    val_s = str(val)
                    src_path = val_s.replace("{lists}", str(self.lists_dir) + "/")
                    src_path = src_path.replace("{bin}", str(self.bin_dir) + "/")
                    src = Path(src_path)
                    if not src.exists() or not src.is_file():
                        continue

                    if src.suffix == ".bin":
                        dst_dir = self.zapret_dir / "files" / "fake"
                        dst_dir.mkdir(parents=True, exist_ok=True)
                        dst = dst_dir / src.name
                        if src.name in copied_bin:
                            continue
                        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                            shutil.copy2(str(src), str(dst))
                        copied_bin.add(src.name)
                    else:
                        dst = zapret_ipset / src.name
                        if src.name in copied_ipset:
                            continue
                        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                            shutil.copy2(str(src), str(dst))
                        copied_ipset.add(src.name)

    def _install_zapret_service_unit(self, strategy_name: str = "") -> None:
        official_service = Path("/etc/systemd/system/zapret.service")
        official_link = self.zapret_dir / "init.d" / "systemd" / "zapret.service"

        if not official_service.exists() and official_link.exists():
            shutil.copy2(str(official_link), str(official_service))
            logger.info("Installed official zapret.service")

        self._fix_init_script_perms()

        try:
            subprocess.run(
                ["systemctl", "daemon-reload"],
                capture_output=True, text=True, timeout=10,
            )
        except Exception as exc:
            logger.warning("daemon-reload failed: %s", exc)

    def _fix_init_script_perms(self) -> None:
        service_file = Path("/etc/systemd/system/zapret.service")
        if service_file.exists():
            try:
                content = service_file.read_text(encoding="utf-8")
                for match in re.finditer(
                    r'^Exec(?:Start|Stop|Reload)\s*=\s*(.+)$', content, re.MULTILINE
                ):
                    cmd_path = match.group(1).strip().split()[0] if match.group(1).strip() else ""
                    if cmd_path and not cmd_path.startswith("-") and not cmd_path.startswith("/usr"):
                        script = Path(cmd_path)
                        if script.exists() and not os.access(str(script), os.X_OK):
                            script.chmod(script.stat().st_mode | 0o111)
                            logger.info("Fixed execute permission on %s", script)
            except Exception as exc:
                logger.warning("Could not fix init script perms: %s", exc)

        ipset_dir = self.zapret_dir / "ipset"
        if ipset_dir.is_dir():
            for sh_file in ipset_dir.glob("*.sh"):
                if not os.access(str(sh_file), os.X_OK):
                    try:
                        sh_file.chmod(sh_file.stat().st_mode | 0o111)
                    except Exception as exc:
                        logger.debug("Failed to fix perms on %s: %s", sh_file, exc)

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

    def _systemd_cmd(self, action: str) -> Tuple[bool, str]:
        try:
            r = subprocess.run(
                ["systemctl", action, "zapret"],
                capture_output=True, text=True, timeout=10,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as exc:
            return (False, str(exc))

    def start_systemd_service(self) -> Tuple[bool, str]:
        return self._systemd_cmd("start")

    def stop_systemd_service(self) -> Tuple[bool, str]:
        return self._systemd_cmd("stop")

    def enable_systemd_service(self) -> Tuple[bool, str]:
        return self._systemd_cmd("enable")

    def disable_systemd_service(self) -> Tuple[bool, str]:
        return self._systemd_cmd("disable")

    def remove_systemd_service(self) -> Tuple[bool, str]:
        try:
            self._systemd_cmd("stop")
            self._systemd_cmd("disable")
            for name in ("zapret.service", "mangopret.service"):
                unit_file = Path("/etc/systemd/system") / name
                if unit_file.exists():
                    unit_file.unlink()
            subprocess.run(["systemctl", "daemon-reload"], capture_output=True, timeout=10)
            return (True, "")
        except Exception as exc:
            return (False, str(exc))

    def _windows_svc_cmd(self, action: str) -> Tuple[bool, str]:
        if not self.is_windows:
            return (False, "Not Windows")
        try:
            r = subprocess.run(
                ["sc", action, "zapret"],
                capture_output=True, text=True, timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
            )
            return (r.returncode == 0, r.stderr.strip() if r.stderr else "")
        except Exception as exc:
            return (False, str(exc))

    def start_windows_service(self) -> Tuple[bool, str]:
        return self._windows_svc_cmd("start")

    def stop_windows_service(self) -> Tuple[bool, str]:
        return self._windows_svc_cmd("stop")

    def service_start(self) -> Tuple[bool, str]:
        if self.is_windows:
            return self.start_windows_service()
        return self.start_systemd_service()

    def service_stop(self) -> Tuple[bool, str]:
        if self.is_windows:
            return self.stop_windows_service()
        return self.stop_systemd_service()

    def service_remove(self) -> Tuple[bool, str]:
        if self.is_windows:
            return self._remove_windows_service()
        return self.remove_systemd_service()

    def _remove_windows_service(self) -> Tuple[bool, str]:
        if not self.is_windows:
            return (False, "Not Windows")
        try:
            for svc in ["zapret", "WinDivert"]:
                subprocess.run(
                    ["net", "stop", svc], capture_output=True,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                )
                subprocess.run(
                    ["sc", "delete", svc], capture_output=True,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                )
            return (True, "")
        except Exception as exc:
            return (False, str(exc))

    def service_install(self, strategy=None, strategy_name: str = "") -> Tuple[bool, str]:
        if self.is_windows:
            return self._install_windows_service(strategy)
        if strategy:
            ok = self.create_systemd_service(strategy, strategy_name)
            return (ok, "" if ok else "Failed to create service")
        return (False, "No strategy provided")

    def _install_windows_service(self, strategy=None) -> Tuple[bool, str]:
        if not self.is_windows:
            return (False, "Not Windows")
        try:
            bin_path = str(self.binary)
            if strategy:
                args = strategy.build_command(
                    str(self.binary), str(self.bin_dir), str(self.lists_dir), True
                )
                cmd_args = " ".join(str(x) for x in args[1:])
                sc_cmd = f'"{bin_path}" {cmd_args}'
            else:
                sc_cmd = f'"{bin_path}"'

            r = subprocess.run(
                ["sc", "create", "zapret", "binPath=", sc_cmd,
                 "DisplayName=", "zapret", "start=", "auto"],
                capture_output=True, text=True, timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
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
                ["journalctl", "-u", "zapret", "-n", str(lines), "--no-pager"],
                capture_output=True, text=True, timeout=10,
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
                    capture_output=True, text=True, timeout=10,
                    creationflags=_WIN_CREATE_NO_WINDOW,
                )
                return r.returncode == 0
            except Exception as exc:
                logger.debug("Startup check failed: %s", exc)
                return False
        else:
            return (Path.home() / ".config" / "autostart" / "mangopret.desktop").exists()

    def enable_startup(self) -> Tuple[bool, str]:
        if self.is_windows:
            return self._enable_startup_windows()
        return self._enable_startup_linux()

    def _enable_startup_linux(self) -> Tuple[bool, str]:
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            dest = autostart_dir / "mangopret.desktop"
            content = (
                "[Desktop Entry]\n"
                "Name=Mangopret\n"
                "Comment=Cross-platform DPI bypass manager\n"
                f'Exec=bash -c \'cd "{self.base_dir}" && ./run_gui.sh --minimized\'\n'
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

    def _enable_startup_windows(self) -> Tuple[bool, str]:
        try:
            gui_bat = self.base_dir / "run_gui.bat"
            if not gui_bat.exists():
                return (False, "run_gui.bat not found")
            cmd = f'cmd.exe /c "cd /d \\"{self.base_dir}\\" && run_gui.bat --minimized"'
            r = subprocess.run(
                ["schtasks", "/create",
                 "/tn", "Mangopret",
                 "/tr", cmd,
                 "/sc", "onlogon",
                 "/rl", "highest",
                 "/f"],
                capture_output=True, text=True, timeout=15,
                creationflags=_WIN_CREATE_NO_WINDOW,
            )
            if r.returncode == 0:
                return (True, "")
            return (False, r.stderr.strip() or r.stdout.strip())
        except Exception as exc:
            return (False, str(exc))

    def disable_startup(self) -> Tuple[bool, str]:
        if self.is_windows:
            return self._disable_startup_windows()
        return self._disable_startup_linux()

    def _disable_startup_linux(self) -> Tuple[bool, str]:
        try:
            dest = Path.home() / ".config" / "autostart" / "mangopret.desktop"
            if dest.exists():
                dest.unlink()
                return (True, "")
            return (False, "Not installed")
        except Exception as exc:
            return (False, str(exc))

    def _disable_startup_windows(self) -> Tuple[bool, str]:
        try:
            r = subprocess.run(
                ["schtasks", "/delete", "/tn", "Mangopret", "/f"],
                capture_output=True, text=True, timeout=10,
                creationflags=_WIN_CREATE_NO_WINDOW,
            )
            if r.returncode == 0:
                return (True, "")
            return (False, r.stderr.strip() or r.stdout.strip())
        except Exception as exc:
            return (False, str(exc))

    # ------------------------------------------------------------------ desktop entry

    def create_desktop_entry(self) -> Tuple[bool, str]:
        if not self.is_linux:
            return (False, "Not Linux")
        try:
            desktop_dir = Path.home() / ".local" / "share" / "applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)
            dest = desktop_dir / "mangopret.desktop"
            src = self.base_dir / "mangopret.desktop"
            if src.exists():
                content = src.read_text(encoding="utf-8")
                content = content.replace(
                    "Exec=run_gui.sh",
                    f'Exec=bash -c \'cd "{self.base_dir}" && ./run_gui.sh\'',
                )
                dest.write_text(content, encoding="utf-8")
                dest.chmod(0o644)
                return (True, str(dest))
            return (False, "mangopret.desktop not found")
        except Exception as exc:
            return (False, str(exc))

    def remove_desktop_entry(self) -> Tuple[bool, str]:
        if not self.is_linux:
            return (False, "Not Linux")
        try:
            dest = Path.home() / ".local" / "share" / "applications" / "mangopret.desktop"
            if dest.exists():
                dest.unlink()
                return (True, "")
            return (False, "Not installed")
        except Exception as exc:
            return (False, str(exc))

    def is_desktop_entry_installed(self) -> bool:
        if not self.is_linux:
            return False
        return (Path.home() / ".local" / "share" / "applications" / "mangopret.desktop").exists()
