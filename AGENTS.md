# Mangopret — AI Agent Guide

Cross-platform (Linux + Windows) GUI/CLI manager for [zapret](https://github.com/bol-van/zapret), a DPI (Deep Packet Inspection) bypass tool. PyQt6 GUI, systemd service management, strategy selection, IP/domain list editing, automated zapret installation.

## Quick Start

```bash
# Linux GUI
./run_gui.sh

# Linux CLI
sudo ./run.sh start "general (EXP)"
sudo ./run.sh stop
sudo ./run.sh fix          # emergency: kill all + clean iptables
sudo ./run.sh status
sudo ./run.sh strategies
sudo ./run.sh service install
sudo ./run.sh service start
```

## Architecture

```
run_gui.sh / run_gui.bat          # auto-installs deps, elevates to root
    |
    v
gui/main_gui.py                   # PyQt6 entry: QApplication + DARK_THEME
gui/main.py                       # CLI entry: argparse subcommands
    |
    v
gui/ui/main_window.py             # QMainWindow — owns all tabs + tray
    |-- gui/ui/tabs/main_tab.py   # Strategy selection, start/stop, status
    |-- gui/ui/tabs/lists_tab.py  # Split-pane list editor
    |-- gui/ui/tabs/service_tab.py# Zapret install, systemd service, iptables, updates
    |-- gui/ui/tabs/log_tab.py    # Timestamped log viewer
    |-- gui/ui/tray.py            # System tray icon + context menu
    |
    v
gui/core/
    platform.py   # PlatformInfo — OS abstraction (process, service, iptables, install)
    strategy.py   # Strategy/StrategyRule/StrategyParser — .strategy JSON + .bat parsing
    config.py     # Config — JSON persistence at ~/.config/mangopret/config.json
    lists.py      # ListManager — domain/IP list CRUD, update, diagnostics
```

## Key Concepts

### Strategies

Strategy files (`gui/strategies/*.strategy`) are JSON defining DPI bypass rules for nfqws/winws. Each strategy has multiple rules separated by `--new`. Path placeholders: `{bin}` → `bin/`, `{lists}` → `lists/`.

```
Strategy.build_command(binary_path, bin_dir, lists_dir, is_windows)
  → flat list of CLI args for nfqws/winws.exe
```

On Windows, the binary is `winws.exe` (renamed nfqws). On Linux, it's `nfqws` from `/opt/zapret/nfq/`.

### iptables Rules (Linux only)

Traffic must be redirected to NFQUEUE for nfqws to process it. Rules go into the `OUTPUT` chain of the `mangle` table:

```
iptables -t mangle -A OUTPUT -p tcp --dport 443 -j NFQUEUE --queue-num 200
```

**CRITICAL**: If nfqws crashes while iptables rules are active, ALL matching traffic is dropped → network dies. Every code path that adds iptables rules MUST have a cleanup path. See "Dangerous Patterns" below.

### Systemd Service

The service (`/etc/systemd/system/mangopret.service`) uses a wrapper script (`/opt/zapret/mangopret-wrapper.sh`) that:
1. Installs iptables rules
2. Runs nfqws in background
3. Cleans up iptables on exit via `trap cleanup EXIT TERM INT`

Mutual exclusion: starting a strategy from GUI kills the service first; starting the service kills the GUI process first.

## File Reference

| File | Purpose |
|------|---------|
| `gui/main.py` | CLI entry point. Subcommands: install, uninstall, start, stop, fix, status, strategies, update, service, lists, diagnostics, convert |
| `gui/main_gui.py` | GUI entry point. Creates QApplication, applies DARK_THEME, instantiates MainWindow |
| `gui/core/platform.py` | OS abstraction: install zapret, start/stop processes, manage systemd/sc services, iptables, journal logs, desktop entries |
| `gui/core/strategy.py` | Strategy/StrategyRule dataclasses, StrategyParser (JSON + .bat), `build_command()` |
| `gui/core/config.py` | Config class: JSON persistence, ipset mode toggling (swaps files with backups) |
| `gui/core/lists.py` | ListManager: list CRUD, ipset/hosts update from GitHub, diagnostics |
| `gui/ui/main_window.py` | MainWindow: orchestrates tabs/tray, strategy start/stop with safety checks, status polling (5s timer) |
| `gui/ui/tray.py` | SystemTray: Strategies submenu, Show/Start/Stop/Fix Network/Quit, auto-start checkbox |
| `gui/ui/theme.py` | DARK_THEME: Tokyo Night QSS stylesheet |
| `gui/ui/tabs/main_tab.py` | MainTab: strategy combo, Start/Stop buttons, status labels, IPSet radio buttons |
| `gui/ui/tabs/service_tab.py` | ServiceTab: zapret install (DownloadThread), systemd service CRUD, iptables apply/remove, updates, diagnostics |
| `gui/ui/tabs/lists_tab.py` | ListsTab: split-pane file editor for list-*.txt and ipset-*.txt |
| `gui/ui/tabs/log_tab.py` | LogTab: timestamped log viewer with copy |
| `gui/strategies/*.strategy` | 21 strategy JSON files (EXP, ALT, ALT2... ALT12, SIMPLE FAKE, FAKE TLS AUTO...) |
| `lists/` | Domain lists (list-general.txt, list-google.txt, etc.) and IP sets (ipset-all.txt, ipset-exclude.txt) |
| `bin/` | Pre-built binaries: nfqws, winws.exe, WinDivert, .bin fake packet templates |
| `silent_install.sh` | Root installer: copies zapret tree to /opt/zapret, runs install_bin.sh + install_prereq.sh |
| `run.sh` | Linux CLI launcher: `exec sudo -E python3 main.py "$@"` |
| `run_gui.sh` | Linux GUI launcher: auto-installs PyQt6, elevates to root, runs main_gui.py |
| `run.bat` / `run_gui.bat` | Windows launchers with bundled Python detection |
| `.github/workflows/release.yml` | Release: bundles portable Python 3.11.9 + PyQt6 for Windows |

## Dangerous Patterns

### iptables Without Cleanup

```python
# BAD: no cleanup if nfqws crashes
self.platform.install_iptables_rules(...)
self.platform.start_process(args)

# GOOD: verify process is alive, clean up if dead
self.platform.install_iptables_rules(...)
self.active_process = self.platform.start_process(args)
QTimer.singleShot(1500, self._verify_started)
```

### Double Execution

Two nfqws instances + two sets of iptables rules = broken network. Always check for and stop conflicting processes before starting:

```python
# Before starting strategy from GUI
svc_status = self.platform.get_service_status()
if svc_status in ("running", "starting"):
    self.platform.service_stop()

# Before starting service
if self.platform.is_process_running():
    self.platform.kill_all()
```

### FORWARD Chain Rules

Only use OUTPUT chain for iptables rules. FORWARD is for routed traffic and dangerous on desktops. FORWARD rules should only ever appear in `remove_iptables_rules()` for cleanup of legacy rules.

## Config System

`~/.config/mangopret/config.json` — all settings. Key fields:
- `ipset_mode`: "none" / "loaded" / "any" (toggled by swapping ipset-all.txt with .backup)
- `nfqueue_num`: "200" (NFQUEUE number for iptables)
- `wf_tcp`: "80,443,2053,2083,2087,2096,8443" (TCP ports for iptables)
- `wf_udp`: "443,19294-19344,50000-50100" (UDP ports for iptables)
- `last_strategy`: name of last used strategy
- `auto_start`: bool, auto-start strategy on GUI launch
- `minimize_to_tray`: bool

## Running Tests

No formal test suite. Verify manually:
1. `python3 -m py_compile gui/core/platform.py` (and each changed file)
2. Launch GUI: `./run_gui.sh` — verify strategy list loads, tabs render
3. Start/stop a strategy — verify iptables rules appear/disappear (`iptables -t mangle -L OUTPUT --line-numbers -n`)
4. `./run.sh status` — verify output
5. Service lifecycle: `./run.sh service install` → `./run.sh service start` → `./run.sh service stop` → `./run.sh service remove`

## Build & Release

Trigger the `release.yml` workflow with a tag input (e.g., `v1.10.0`). It bundles:
- `gui/`, `lists/`, `bin/`, `.service/`, scripts, `mangopret.desktop`
- `python/` (portable Python 3.11.9 with PyQt6 pre-installed for Windows)

Produces `.zip` and `.tar.gz` archives with SHA256 checksums.

## Dependencies

- **Linux**: Python 3, PyQt6 (auto-installed by run_gui.sh), iptables, root access
- **Windows**: Python 3 (bundled or system), PyQt6, WinDivert (included in bin/)
- **No pip requirements.txt** — PyQt6 is the only Python dependency, installed by the launcher scripts
