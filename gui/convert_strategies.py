#!/usr/bin/env python3
"""
Mangopret Strategy Converter
Converts zapret-discord-youtube .bat strategy files to universal .strategy JSON format.

Usage:
    python convert_strategies.py                          # auto-detect bat dir, output to gui/strategies/
    python convert_strategies.py --bat-dir /path/to/bats  # specify bat directory
    python convert_strategies.py --output /path/to/out    # specify output directory
    python convert_strategies.py --verify                 # verify existing .strategy files
    python convert_strategies.py --single file.bat        # convert a single .bat file
"""
import sys
import os
import json
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))

from core.strategy import StrategyParser, Strategy


def print_banner():
    print("=" * 60)
    print("  Mangopret Strategy Converter")
    print("  Converts .bat -> .strategy (universal JSON format)")
    print("=" * 60)
    print()


def convert_all(bat_dir: Path, output_dir: Path):
    print(f"  Source:  {bat_dir}")
    print(f"  Output:  {output_dir}")
    print()

    converted = StrategyParser.convert_all_bats(str(bat_dir), str(output_dir))

    print()
    print("-" * 60)
    print(f"  Converted: {len(converted)} strategies")
    print()

    for s in converted:
        rules_summary = []
        for r in s.rules:
            desync = r.params.get("dpi-desync", "?")
            if isinstance(desync, list):
                desync = desync[0]
            rules_summary.append(f"{r.name} ({desync})")
        print(f"  [{s.id}]")
        print(f"    Name:        {s.name}")
        print(f"    Description: {s.description}")
        print(f"    Rules:       {len(s.rules)}")
        for rs in rules_summary:
            print(f"      - {rs}")
        print()

    return converted


def convert_single(bat_path: Path, output_dir: Path):
    print(f"  Converting: {bat_path.name}")
    strategy = StrategyParser._from_bat(bat_path)
    if not strategy or not strategy.rules:
        print(f"  FAILED: Could not parse {bat_path.name}")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{strategy.id}.strategy"
    StrategyParser.to_strategy_file(strategy, out_path)

    print(f"  Output: {out_path}")
    print(f"  Name:   {strategy.name}")
    print(f"  Rules:  {len(strategy.rules)}")
    for r in strategy.rules:
        desync = r.params.get("dpi-desync", "?")
        print(f"    - {r.name}: {desync}")

    return strategy


def verify_strategies(strategies_dir: Path):
    print(f"  Verifying strategies in: {strategies_dir}")
    print()

    files = sorted(strategies_dir.glob("*.strategy"))
    ok = 0
    errors = 0

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            required = ["id", "name", "rules"]
            missing = [k for k in required if k not in data]
            if missing:
                print(f"  [WARN] {f.name}: missing fields: {missing}")
                errors += 1
                continue

            rules = data.get("rules", [])
            if not rules:
                print(f"  [WARN] {f.name}: no rules")
                errors += 1
                continue

            for i, rule in enumerate(rules):
                if "name" not in rule:
                    print(f"  [WARN] {f.name}: rule {i} has no name")

            print(f"  [OK]   {f.name}: {data.get('name', '?')} ({len(rules)} rules)")
            ok += 1

        except json.JSONDecodeError as e:
            print(f"  [ERR]  {f.name}: invalid JSON: {e}")
            errors += 1
        except Exception as e:
            print(f"  [ERR]  {f.name}: {e}")
            errors += 1

    print()
    print(f"  Results: {ok} OK, {errors} errors")
    return errors == 0


def diff_with_bats(bat_dir: Path, strategy_dir: Path):
    print(f"  Comparing .bat files with .strategy files")
    print(f"  BAT dir:     {bat_dir}")
    print(f"  Strategy dir: {strategy_dir}")
    print()

    bat_files = {f.stem: f for f in bat_dir.glob("general*.bat")}
    strat_files = {f.stem: f for f in strategy_dir.glob("*.strategy")}

    only_bat = set(bat_files.keys()) - set(strat_files.keys())
    only_strat = set(strat_files.keys()) - set(bat_files.keys())
    both = set(bat_files.keys()) & set(strat_files.keys())

    if only_bat:
        print(f"  BAT files without .strategy ({len(only_bat)}):")
        for name in sorted(only_bat):
            print(f"    - {bat_files[name].name}")
        print()

    if only_strat:
        print(f"  .strategy files without .bat ({len(only_strat)}):")
        for name in sorted(only_strat):
            print(f"    - {strat_files[name].name}")
        print()

    print(f"  Matched: {len(both)} files")
    for name in sorted(both):
        print(f"    - {name}")

    return len(only_bat) == 0


def main():
    parser = argparse.ArgumentParser(
        description="Mangopret Strategy Converter: .bat -> .strategy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--bat-dir", type=str, default=None,
                        help="Directory containing .bat files (default: auto-detect)")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output directory for .strategy files (default: gui/strategies/)")
    parser.add_argument("--verify", action="store_true",
                        help="Verify existing .strategy files instead of converting")
    parser.add_argument("--single", type=str, default=None,
                        help="Convert a single .bat file")
    parser.add_argument("--diff", action="store_true",
                        help="Compare .bat files with existing .strategy files")

    args = parser.parse_args()

    print_banner()

    bat_dir = Path(args.bat_dir) if args.bat_dir else BASE_DIR
    output_dir = Path(args.output) if args.output else SCRIPT_DIR / "strategies"

    if args.verify:
        success = verify_strategies(output_dir)
        return 0 if success else 1

    if args.single:
        bat_path = Path(args.single)
        if not bat_path.exists():
            bat_path = bat_dir / args.single
        if not bat_path.exists():
            print(f"  File not found: {args.single}")
            return 1
        convert_single(bat_path, output_dir)
        return 0

    if args.diff:
        diff_with_bats(bat_dir, output_dir)
        return 0

    converted = convert_all(bat_dir, output_dir)

    if converted:
        print("-" * 60)
        print(f"  Done! {len(converted)} .strategy files written to:")
        print(f"  {output_dir}")
        print()

    verify_strategies(output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
