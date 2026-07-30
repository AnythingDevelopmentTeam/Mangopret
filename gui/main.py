#!/usr/bin/env python3
import argparse
import os
import sys

try:
    import argcomplete
except ImportError:
    argcomplete = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, SCRIPT_DIR)

from core.config import Config
from core.log import get_logger
from core.platform import PlatformInfo
from core.strategy import StrategyParser

from gui import APP_VERSION

logger = get_logger(__name__)

BANNER = rf"""
  __  __                         _____          _
 |  \/  |                       |  __ \        | |
 | \  / | __ _ _ __   __ _  ___ | |__) | __ ___| |_
 | |\/| |/ _` | '_ \ / _` |/ _ \|  ___/ '__/ _ \ __|
 | |  | | (_| | | | | (_| | (_) | |   | | |  __/ |_
 |_|  |_|\__,_|_| |_|\__, |\___/|_|   |_|  \___|\__|
                      __/ |
                     |___/                           v{APP_VERSION}

"""


def get_platform() -> PlatformInfo:
    return PlatformInfo(BASE_DIR)


def get_config() -> Config:
    p = get_platform()
    return Config(str(p.config_dir))


def cmd_install(args: argparse.Namespace) -> None:
    p = get_platform()
    if p.is_windows:
        print("Zapret is already bundled with Mangopret on Windows.")
        return

    print("Installing zapret to /opt/zapret ...")
    ok = p.install_zapret(callback=lambda m: print(f"  {m}"))
    if not ok:
        print("Installation failed.")
        sys.exit(1)

    print("\nZapret2 installed. You can now use:")
    print("  ./run.sh start <strategy>   - start a strategy")
    print("  ./run.sh status             - show status")
    print("  ./run.sh strategies         - list strategies")


def cmd_uninstall(args: argparse.Namespace) -> None:
    p = get_platform()
    print("Stopping zapret ...")
    p.kill_all()

    print("Removing systemd service ...")
    p.remove_systemd_service()

    zapret_dir = p.zapret_dir
    if zapret_dir.exists():
        reply = input(f"Delete {zapret_dir}? [y/N] ").strip().lower()
        if reply == "y":
            import shutil

            shutil.rmtree(zapret_dir)
            print(f"Removed {zapret_dir}")
        else:
            print("Skipped removal")
    else:
        print(f"{zapret_dir} not found, nothing to remove")


def cmd_start(args: argparse.Namespace) -> None:
    p = get_platform()
    config = get_config()

    if not p.is_zapret_installed():
        print("Zapret is not installed. Run: ./run.sh install")
        sys.exit(1)

    name = args.strategy
    strategies = _load_strategies(p)
    if name not in strategies:
        print(f"Unknown strategy: {name}")
        print(f"Available: {', '.join(strategies.keys())}")
        sys.exit(1)

    _stop_running(p)

    if p.is_linux:
        svc_status = p.get_service_status()
        if svc_status in ("running", "starting"):
            print("Stopping systemd service to avoid conflict...")
            p.service_stop()

    strategy = strategies[name]
    auto_hostlist = config.get("auto_hostlist", False)
    ipcache = config.get("ipcache", False)
    args_list = strategy.build_command(
        binary_path=str(p.binary),
        bin_dir=str(p.bin_dir),
        lists_dir=str(p.lists_dir),
        is_windows=p.is_windows,
        auto_hostlist=auto_hostlist,
        ipcache=ipcache,
    )

    print(f"Starting: {name}")
    if not p.is_windows:
        print("Validating config with --dry-run...")
        ok, msg = p.validate_binary_dry_run(args_list)
        if not ok:
            print(f"Config validation FAILED: {msg}")
            sys.exit(1)
        print("Config valid.")

    if p.is_linux:
        config.set("last_strategy", name)
        print("Writing zapret config and starting service...")
        ok = p.create_systemd_service(strategy, name)
        if not ok:
            print("Failed to write zapret config")
            sys.exit(1)
        ok, err = p.service_start()
        if ok:
            print(f"Service started with strategy: {name}")
        else:
            print(f"Failed to start service: {err}")
            sys.exit(1)
    else:
        proc = p.start_process(args_list)
        if proc:
            import time

            time.sleep(1.5)
            if proc.poll() is not None:
                print(
                    f"FAILED: nfqws2 crashed immediately (exit code: {proc.returncode})"
                )
                sys.exit(1)
            print(f"Process started (PID: {proc.pid})")
            config.set("last_strategy", name)
        else:
            print("Failed to start process")
            sys.exit(1)


def cmd_stop(args: argparse.Namespace) -> None:
    p = get_platform()
    print("Stopping ...")
    if p.is_linux:
        ok, err = p.service_stop()
        print("Service stopped." if ok else f"Failed: {err}")
    else:
        p.kill_all()
        print("Stopped.")


def cmd_fix(args: argparse.Namespace) -> None:
    p = get_platform()
    print("Emergency: fixing network...")
    p.kill_all()
    p.service_stop()
    print("All nfqws2 killed, network cleaned.")


def cmd_status(args: argparse.Namespace) -> None:
    p = get_platform()
    config = get_config()

    print(f"Zapret installed: {'yes' if p.is_zapret_installed() else 'no'}")
    if p.is_zapret_installed():
        print(f"Zapret path: {p.zapret_dir}")
        print(f"Binary: {p.binary}")

    running = p.is_process_running()
    print(f"Process: {'RUNNING' if running else 'stopped'}")

    svc = p.get_service_status()
    print(f"Service: {svc}")

    ipset = config.get_ipset_mode(str(p.lists_dir))
    print(f"IPSet: {ipset}")


def cmd_strategies(args: argparse.Namespace) -> None:
    p = get_platform()
    strategies = _load_strategies(p)
    if not strategies:
        print("No strategies found.")
        return
    print("Available strategies:")
    for name in sorted(strategies.keys()):
        s = strategies[name]
        print(f"  {name}")
        print(f"    {s.description}")


def cmd_update(args: argparse.Namespace) -> None:
    p = get_platform()
    if p.is_windows:
        print("Zapret is already bundled with Mangopret on Windows.")
        return

    if not p.is_zapret_installed():
        print("Zapret is not installed. Run: ./run.sh install")
        sys.exit(1)

    print("Updating zapret ...")
    ok = p.install_zapret(callback=lambda m: print(f"  {m}"))
    if ok:
        print("Update complete.")
    else:
        print("Update failed.")
        sys.exit(1)


def cmd_service(args: argparse.Namespace) -> None:
    p = get_platform()
    config = get_config()
    action = args.action

    if not p.is_zapret_installed():
        print("Zapret is not installed. Run: ./run.sh install")
        sys.exit(1)

    if action == "install":
        name = config.get("last_strategy", "")
        strategies = _load_strategies(p)
        if name in strategies:
            strategy = strategies[name]
            ok, err = p.service_install(strategy, name)
            if ok:
                print(f"Service created for: {name}")
            else:
                print(f"Failed: {err}" if err else "Failed to create service")
        else:
            print("No strategy selected. Start a strategy first, then install service.")
    elif action == "remove":
        ok, err = p.service_remove()
        print("Service removed." if ok else f"Failed: {err}")
    elif action == "start":
        if p.is_process_running():
            print("Stopping GUI-managed process to avoid conflict...")
            p.kill_all()
        ok, err = p.service_start()
        print("Service started." if ok else f"Failed: {err}")
    elif action == "stop":
        ok, err = p.service_stop()
        print("Service stopped." if ok else f"Failed: {err}")
    elif action == "enable":
        ok, err = p.enable_systemd_service()
        print("Auto-start enabled." if ok else f"Failed: {err}")
    elif action == "disable":
        ok, err = p.disable_systemd_service()
        print("Auto-start disabled." if ok else f"Failed: {err}")
    elif action == "log":
        logs = p.get_journal_logs(50)
        print(logs if logs else "No logs found.")
    else:
        print(f"Unknown action: {action}")


def cmd_lists(args: argparse.Namespace) -> None:
    p = get_platform()
    from core.lists import ListManager

    lm = ListManager(str(p.lists_dir), str(p.utils_dir))

    action = args.action
    if action == "update-strategies":
        ok = lm.update_strategies(
            str(p.strategies_dir), callback=lambda m: print(f"  {m}")
        )
        print("Strategies updated." if ok else "Failed to update strategies.")
    elif action == "update-ipset":
        ok = lm.update_ipset(callback=lambda m: print(f"  {m}"))
        print("IPSet updated." if ok else "Failed to update IPSet.")
    elif action == "update-hosts":
        ok = lm.update_hosts(callback=lambda m: print(f"  {m}"))
        print("Hosts updated." if ok else "Hosts already up to date.")
    elif action == "edit":
        filename = args.file
        if not filename:
            print("Available lists:")
            for f in lm.get_list_files():
                print(f"  {f}")
            return
        content = lm.read_list(filename)
        if not content:
            print(f"File not found: {filename}")
            return
        print(f"--- {filename} ---")
        print(content)
    else:
        print("Available lists:")
        for f in lm.get_list_files():
            print(f"  {f}")


def cmd_diagnostics(args: argparse.Namespace) -> None:
    p = get_platform()
    from core.lists import ListManager

    lm = ListManager(str(p.lists_dir), str(p.utils_dir))
    result = lm.run_diagnostics(p.is_windows)
    print(result)


def cmd_convert(args: argparse.Namespace) -> None:
    from pathlib import Path

    from core.strategy import StrategyParser

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    files_to_convert: list[Path] = []

    if input_path.is_file():
        files_to_convert.append(input_path)
    elif input_path.is_dir():
        for ext in ("*.bat", "*.strategy"):
            files_to_convert.extend(sorted(input_path.glob(ext)))
        if not files_to_convert:
            print(f"No .bat or .strategy files found in {input_path}")
            return
    else:
        print(f"Not found: {input_path}")
        return

    converted = 0
    failed = 0

    for f in files_to_convert:
        print(f"  {f.name} ... ", end="", flush=True)

        if f.suffix == ".bat":
            strategy = StrategyParser._from_bat(f)
        elif f.suffix == ".strategy":
            strategy = StrategyParser._from_json(f)
        else:
            print("SKIP (unknown type)")
            continue

        if not strategy or not strategy.rules:
            print("FAILED (no rules parsed)")
            failed += 1
            continue

        out_path = output_dir / f"{strategy.id}.strategy"
        StrategyParser.to_strategy_file(strategy, out_path)
        print(f"OK -> {out_path.name} ({len(strategy.rules)} rules)")
        converted += 1

    print(f"\nDone: {converted} converted, {failed} failed")
    print(f"Output: {output_dir}")


def cmd_completion(args: argparse.Namespace) -> None:
    shell = args.shell
    try:
        import argcomplete

        # Register for both run.sh and python3 -m gui.main
        code = argcomplete.shellcode(
            [shell], "run.sh", argcomplete.argparse_wrapper("python3 -m gui.main")
        )
        print(code)
        print(f'# Run: eval "$({code})"', file=sys.stderr)
    except ImportError:
        print(
            "argcomplete not installed. Run: pip install mangopret[completion]",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_version(args: argparse.Namespace) -> None:
    from core.update import check_mangopret_update

    print(f"Mangopret v{APP_VERSION}")
    result = check_mangopret_update()
    if result:
        _, latest, _ = result
        if latest == APP_VERSION:
            print(f"You are up to date (latest: {latest})")
        else:
            print(f"UPDATE AVAILABLE: {latest}")
    else:
        print("Update check failed (no network?)")


def _load_strategies(p: PlatformInfo) -> dict:
    strategies: dict = {}
    if p.strategies_dir.exists():
        for f in sorted(p.strategies_dir.glob("*.strategy")):
            s = StrategyParser.from_file(str(f))
            if s and s.rules:
                strategies[s.name] = s
    return strategies


def _stop_running(p: PlatformInfo) -> None:
    if p.is_process_running():
        print("Stopping current process ...")
        p.kill_all()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="run.sh",
        description="Mangopret - zapret DPI bypass manager",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", help="Download and install zapret to /opt/zapret")
    sub.add_parser("uninstall", help="Remove zapret")
    sub.add_parser("status", help="Show current status")
    sub.add_parser("strategies", help="List available strategies")
    sub.add_parser("update", help="Update zapret to latest version")
    sub.add_parser("stop", help="Stop running bypass")
    sub.add_parser("fix", help="Emergency: kill all nfqws2 and clean iptables")
    sub.add_parser("diagnostics", help="Run diagnostics")

    p_convert = sub.add_parser(
        "convert", help="Convert .bat or zapret config files to .strategy"
    )
    p_convert.add_argument(
        "input", help="Input .bat file or directory containing .bat/.strategy files"
    )
    p_convert.add_argument(
        "-o",
        "--output",
        default="strategies",
        help="Output directory for .strategy files (default: strategies)",
    )

    p_start = sub.add_parser("start", help="Start a strategy")
    p_start.add_argument("strategy", nargs="?", default="", help="Strategy name")

    p_svc = sub.add_parser("service", help="Manage systemd service")
    p_svc.add_argument(
        "action",
        choices=["install", "remove", "start", "stop", "enable", "disable", "log"],
    )

    p_lists = sub.add_parser("lists", help="Manage domain/IP lists")
    p_lists.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "update-strategies", "update-ipset", "update-hosts", "edit"],
    )
    p_lists.add_argument("file", nargs="?", default=None)

    sub.add_parser("version", help="Show version and check for updates")

    try:
        import argcomplete
    except ImportError:
        argcomplete = None
    else:
        p_completion = sub.add_parser(
            "completion", help="Generate shell completion script"
        )
        p_completion.add_argument(
            "shell", choices=["bash", "zsh", "fish"], help="Target shell"
        )

    if argcomplete:
        argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.version:
        cmd_version(args)
        return

    if not args.command:
        print(BANNER)
        parser.print_help()
        return

    commands = {
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "start": cmd_start,
        "stop": cmd_stop,
        "fix": cmd_fix,
        "status": cmd_status,
        "strategies": cmd_strategies,
        "version": cmd_version,
        "update": cmd_update,
        "service": cmd_service,
        "lists": cmd_lists,
        "diagnostics": cmd_diagnostics,
        "convert": cmd_convert,
        "completion": cmd_completion,
    }

    func = commands.get(args.command)
    if func:
        func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
