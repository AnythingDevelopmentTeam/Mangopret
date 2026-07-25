# Mangopret

Cross-platform GUI/CLI manager for [zapret](https://github.com/bol-van/zapret) — a DPI (Deep Packet Inspection) bypass tool. PyQt6 GUI, systemd service management, strategy selection, IP/domain list editing, automated installation.

> **Fork notice**: This is an independent fork of the original Mangopret project. We are not affiliated with nor endorsed by the original maintainers.

## Features

- Graphical interface (PyQt6) and CLI management of zapret
- 27+ pre-configured DPI bypass strategies
- Systemd service management (install, start, stop, remove)
- iptables NFQUEUE rules for traffic redirection
- Domain/IP list editing with split-pane editor
- IPSet mode switching
- System tray integration with quick controls
- Automated zapret installation
- Self-updating IP sets and hosts lists
- Cross-platform (Windows + Linux)

## Quick Start

### Linux

```bash
# Run GUI (auto-installs dependencies, elevates to root)
./run_gui.sh

# Run CLI
sudo ./run.sh start "general (EXP)"
sudo ./run.sh stop
sudo ./run.sh fix           # emergency: kill all + clean iptables
sudo ./run.sh status
sudo ./run.sh strategies
sudo ./run.sh service install
sudo ./run.sh service start
```

### Windows

```cmd
run_gui.bat     # GUI launcher
run.bat start "general (EXP)"
run.bat stop
```

## Documentation

See [AGENTS.md](./AGENTS.md) for full architecture, dangerous patterns, config system, and file reference.

## License

MIT
