# CLAUDE.md — Mangopret

Cross-platform DPI bypass manager for zapret. PyQt6 GUI + CLI on Linux/Windows.

## Project Layout

```
gui/
  main.py              # CLI (argparse): install, start, stop, fix, status, service, lists
  main_gui.py          # GUI (PyQt6): QApplication + DARK_THEME
  core/
    platform.py        # PlatformInfo — ALL OS ops (install, process, service, iptables, journal)
    strategy.py        # Strategy/StrategyRule dataclasses + StrategyParser (.strategy JSON + .bat)
    config.py          # Config — JSON at ~/.config/mangopret/config.json
    lists.py           # ListManager — list CRUD, ipset/hosts update, diagnostics
  ui/
    main_window.py     # MainWindow — tabs + tray + strategy lifecycle + 5s status timer
    tray.py            # SystemTray — context menu, signals
    theme.py           # DARK_THEME QSS (Tokyo Night)
    tabs/
      main_tab.py      # Strategy combo, Start/Stop, status, IPSet radio buttons
      service_tab.py   # Zapret install, systemd service, iptables, updates, diagnostics
      lists_tab.py     # Split-pane file editor
      log_tab.py       # Timestamped log
  strategies/*.strategy  # 21 DPI bypass strategy JSON files
bin/                   # nfqws, winws.exe, WinDivert, .bin fake templates
lists/                 # Domain lists + IP sets
run.sh / run_gui.sh    # Linux launchers (auto-elevate to root)
run.bat / run_gui.bat  # Windows launchers (bundled Python detection)
silent_install.sh      # Root installer → /opt/zapret
```

## How It Works

### Strategy Execution Flow

1. User picks strategy → `Strategy.build_command()` builds nfqws CLI args
2. On Linux: `install_iptables_rules()` adds OUTPUT chain rules redirecting traffic to NFQUEUE
3. `start_process()` spawns nfqws
4. After 1.5s, `_verify_started()` checks if nfqws is alive — if dead, iptables rules are removed immediately
5. Every 5s, `_refresh_status()` checks process health — if process died unexpectedly, iptables are cleaned

### Service Mode

Systemd service uses a wrapper script (`/opt/zapret/mangopret-wrapper.sh`) that:
- Sets up iptables rules before nfqws
- Runs nfqws in background
- Cleans up iptables on exit via `trap cleanup EXIT TERM INT`

### Mutual Exclusion

**Never run two nfqws instances simultaneously.** Before starting:
- GUI strategy start → stops systemd service first
- Service start → kills GUI-managed nfqws first
- CLI `start` → stops service if running
- CLI `service start` → kills GUI process if running

### iptables Safety

Rules go in OUTPUT chain only (never FORWARD on desktop). If nfqws crashes with rules active, all matching traffic is dropped → network dies. Every code path that adds rules MUST clean them up on failure.

## Dangerous Patterns to Avoid

```python
# WRONG: iptables rules stay if process dies
self.platform.install_iptables_rules(...)
self.platform.start_process(args)

# RIGHT: verify + cleanup on failure
self.platform.install_iptables_rules(...)
self.active_process = self.platform.start_process(args)
QTimer.singleShot(1500, self._verify_started)

# WRONG: double execution
# Both GUI process and systemd service running = doubled iptables + two nfqws

# RIGHT: stop the other mode first
svc_status = self.platform.get_service_status()
if svc_status in ("running", "starting"):
    self.platform.service_stop()
```

## Config

`~/.config/mangopret/config.json`:
- `nfqueue_num`: "200"
- `wf_tcp`: "80,443,2053,2083,2087,2096,8443"
- `wf_udp`: "443,19294-19344,50000-50100"
- `ipset_mode`: "none" / "loaded" / "any"
- `last_strategy`, `auto_start`, `minimize_to_tray`

## Verify Changes

```bash
python3 -m py_compile gui/core/platform.py
python3 -m py_compile gui/ui/main_window.py
# ... compile each changed file
./run_gui.sh   # launch and test
```

## Key Facts

- Only Python dependency is PyQt6 (auto-installed by launcher scripts)
- zapret installed to `/opt/zapret` (Linux) via `silent_install.sh`
- Binary resolution: `nfq/nfqws` → `bin/nfqws` → `binaries/linux-x86_64/nfqws`
- `.strategy` JSON path placeholders: `{bin}` → `bin/`, `{lists}` → `lists/`
- Windows uses `winws.exe` (renamed nfqws) + WinDivert for packet interception
- Release workflow bundles portable Python 3.11.9 + PyQt6 for Windows
