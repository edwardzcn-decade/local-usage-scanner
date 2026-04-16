from __future__ import annotations

import json

from scanner.models import ScanReport


def format_scan_json(report: ScanReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)