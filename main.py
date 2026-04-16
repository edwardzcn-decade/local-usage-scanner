import argparse

from scanner.models import ScanReport
from scanner.engine import run_scan
from formatters.text_formatter import format_scan_text


def build_parser():
    parser = argparse.ArgumentParser(description="A minimal local app storage demo.")
    return parser


def main():
    parser = build_parser()
    parser.parse_args()

    report: ScanReport = run_scan()
    output: str = format_scan_text(report)
    print(output)


if __name__ == "__main__":
    main()
