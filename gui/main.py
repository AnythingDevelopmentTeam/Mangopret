#!/usr/bin/env python3
"""Mangopret - CLI manager for zapret DPI bypass."""
import sys
import os
import argparse
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, SCRIPT_DIR)

from core.platform import PlatformInfo
from core.config import Config
from core.strategy import StrategyParser


BANNER = r"""
  __  __                         _____          _   
 |  \/  |                       |  __ \        | |  
 | \  / | __ _ _ __   __ _  ___ | |__) | __ ___| |_ 
 | |\/| |/ _` | '_ \ / _` |/ _ \|  ___/ '__/ _ \ __|
 | |  | | (_| | | | | (_| | (_) | |   | | |  __/ |_ 
 |_|  |_|\__,_|_| |_|\__, |\___/|_|   |_|  \___|\__|
                      __/ |                         
                     |___/                           v%s

""" % "2.0"


def get_platform():
    return PlatformInfo(BASE_DIR)


def get_config():
    p = get_platform()
    return Config(str(p.config_dir))


def cmd_install(args):
    p = get_platform()
    config = get_config()

    print("Installing zapret to /opt/zapret ...")
    ok = p.install_zapret(callback=lambda m: print(f"  {m}"))
    if not ok:
        print("Installation failed.")
        sys.exit(1)

    print("\nZapret installed. You can now use:")
    print("  ./run.sh start <strategy>   - start a strategy")
    print("  ./run.sh status             - show status")
    print("  ./run.sh strategies         - list strategies")


def cmd_uninstall(args):
    p = get_platform()
    print("Stopping zapret ...")
    p.kill_all()
    p.remove_iptables_rules()

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
            print("Skipped removal of /opt/zapret")
    else:
        print(f"{zapret_dir} not found, nothing to remove")


def cmd_start(args):
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

    strategy = strategies[name]
    args_list = strategy.build_command(
        binary_path=str(p.binary),
        bin_dir=str(p.bin_dir),
        lists_dir=str(p.lists_dir),
        game_filter_tcp=config.game_filter_tcp,
        game_filter_udp=config.game_filter_udp,
        is_windows=p.is_windows,
    )

    print(f"Starting: {name}")
    if p.is_linux:
        wf_tcp = config.get("wf_tcp", "80,443,2053,2083,2087,2096,8443")
        wf_udp = config.get("wf_udp", "443,19294-19344,50000-50100")
        queue_num = config.get("nfqueue_num", "200")
        results = p.install_iptables_rules(wf_tcp, wf_udp, queue_num)
        applied = sum(1 for _, ok, _ in results if ok)
        print(f"iptables: {applied}/{len(results)} rules applied")

    proc = p.start_service(name, args_list)
    if proc:
        print(f"Process started (PID: {proc.pid})")
        config.set("last_strategy", name)
    else:
        print("Failed to start process")
        sys.exit(1)


def cmd_stop(args):
    p = get_platform()
    print("Stopping ...")
    p.kill_all()
    p.remove_iptables_rules()
    print("Stopped.")


def cmd_status(args):
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

    gf = config.get("game_filter", "disabled")
    ipset = config.get_ipset_mode(str(p.lists_dir))
    print(f"Game filter: {gf}")
    print(f"IPSet: {ipset}")


def cmd_strategies(args):
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


def cmd_update(args):
    p = get_platform()
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


def cmd_service(args):
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
            cmd_list = strategy.build_command(
                binary_path=str(p.binary),
                bin_dir=str(p.bin_dir),
                lists_dir=str(p.lists_dir),
                game_filter_tcp=config.game_filter_tcp,
                game_filter_udp=config.game_filter_udp,
                is_windows=p.is_windows,
            )
            ok = p.create_systemd_service(cmd_list, name)
            if ok:
                print(f"Systemd service created for: {name}")
            else:
                print("Failed to create service (need root?)")
        else:
            print("No strategy selected. Start a strategy first, then install service.")
    elif action == "remove":
        ok, err = p.remove_systemd_service()
        print("Service removed." if ok else f"Failed: {err}")
    elif action == "start":
        ok, err = p.start_systemd_service()
        print("Service started." if ok else f"Failed: {err}")
    elif action == "stop":
        ok, err = p.stop_systemd_service()
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


def cmd_lists(args):
    p = get_platform()
    config = get_config()
    from core.lists import ListManager
    lm = ListManager(str(p.lists_dir), str(p.utils_dir))

    action = args.action
    if action == "update-ipset":
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


def cmd_diagnostics(args):
    p = get_platform()
    from core.lists import ListManager
    lm = ListManager(str(p.lists_dir), str(p.utils_dir))
    result = lm.run_diagnostics(p.is_windows)
    print(result)


def _load_strategies(p):
    strategies = {}
    if p.strategies_dir.exists():
        for f in sorted(p.strategies_dir.glob("*.strategy")):
            s = StrategyParser.from_file(str(f))
            if s and s.rules:
                strategies[s.name] = s
    return strategies


def _stop_running(p):
    if p.is_process_running():
        print("Stopping current process ...")
        p.kill_all()
        p.remove_iptables_rules()


def main():
    parser = argparse.ArgumentParser(
        prog="run.sh",
        description="Mangopret - zapret DPI bypass manager",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", help="Download and install zapret to /opt/zapret")
    sub.add_parser("uninstall", help="Remove zapret")
    sub.add_parser("status", help="Show current status")
    sub.add_parser("strategies", help="List available strategies")
    sub.add_parser("update", help="Update zapret to latest version")
    sub.add_parser("stop", help="Stop running bypass")
    sub.add_parser("diagnostics", help="Run diagnostics")

    p_start = sub.add_parser("start", help="Start a strategy")
    p_start.add_argument("strategy", nargs="?", default="", help="Strategy name")

    p_svc = sub.add_parser("service", help="Manage systemd service")
    p_svc.add_argument("action", choices=[
        "install", "remove", "start", "stop", "enable", "disable", "log"
    ])

    p_lists = sub.add_parser("lists", help="Manage domain/IP lists")
    p_lists.add_argument("action", nargs="?", default="list",
                         choices=["list", "update-ipset", "update-hosts", "edit"])
    p_lists.add_argument("file", nargs="?", default=None)

    args = parser.parse_args()

    if not args.command:
        print(BANNER)
        parser.print_help()
        return

    commands = {
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "strategies": cmd_strategies,
        "update": cmd_update,
        "service": cmd_service,
        "lists": cmd_lists,
        "diagnostics": cmd_diagnostics,
    }

    func = commands.get(args.command)
    if func:
        func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
