#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from formatters.json_formatter import format_scan_json
from formatters.text_formatter import format_scan_text
from scanner.engine import run_scan
from scanner.platforms import detect_platform, normalize_platform
from scanner.rules import load_rules


def get_default_rules_path(platform_name: str) -> Path:
    rules_dir = Path(__file__).resolve().parent / "rules"
    if platform_name == "macos":
        return rules_dir / "default_macos_apps_max.json"
    if platform_name == "windows":
        return rules_dir / "default_windows_apps.json"
    return rules_dir / "default_linux_apps.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only local app storage usage scanner. "
            "Scans configured application directories and reports size by category."
        )
    )
    parser.add_argument(
        "--only",
        nargs="+",
        help="Only scan the specified app ids or names, for example: --only slack notion",
    )
    parser.add_argument(
        "--platform",
        help="Override detected platform. Supported values: macos, linux, windows, wsl",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Default: text",
    )
    parser.add_argument(
        "--rules",
        help="Path to a rule file or directory containing JSON rule files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show additional scan notes and non-fatal errors",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    detected_platform = detect_platform()
    try:
        target_platform = normalize_platform(args.platform) if args.platform else detected_platform
    except ValueError as exc:
        parser.error(str(exc))

    if args.rules:
        rules_path = Path(args.rules).expanduser()
    else:
        rules_path = get_default_rules_path(target_platform)

    rule_load = load_rules(rules_path)
    report = run_scan(
        rules=rule_load.rules,
        platform_name=target_platform,
        selected_apps=args.only or [],
        verbose=args.verbose,
        rules_source=str(rules_path),
        detected_platform=detected_platform,
    )
    report.global_notes = rule_load.notes + report.global_notes
    report.rules_loaded = len(rule_load.rules)
    if not rule_load.rules:
        report.global_notes.append("No valid rules were loaded, so nothing was scanned.")

    if args.format == "json":
        print(format_scan_json(report))
    else:
        print(format_scan_text(report, verbose=args.verbose))

    return 0


if __name__ == "__main__":
    sys.exit(main())
