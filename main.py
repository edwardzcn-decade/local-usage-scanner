import argparse

from scanner.models import ScanReport
from scanner.engine import run_scan
from scanner.rules import load_rules
from formatters.text_formatter import format_scan_text


def build_parser():
    parser = argparse.ArgumentParser(description="A minimal local app storage demo.")
    parser.add_argument(
        "--rules",
        default="rules/default_macos_apps.json",
        help="Path to the JSON rules file",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    rules = load_rules(args.rules)
    report: ScanReport = run_scan(rules=rules)
    output: str = format_scan_text(report)
    print(output)


if __name__ == "__main__":
    main()
