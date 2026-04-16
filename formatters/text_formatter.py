from __future__ import annotations

from scanner.models import AppScanResult, PathScanResult, ScanReport
from scanner.utils import format_bytes


def format_scan_text(report: ScanReport, verbose: bool = False) -> str:
    lines: list[str] = []

    lines.append(
        f"# app-storage-scanner ({report.tool_mode}, detected={report.detected_platform}, target={report.target_platform})"
    )
    lines.append("")

    if report.global_notes:
        for note in report.global_notes:
            lines.append(f"[INFO ] {note}")
        lines.append("")

    for app_result in report.app_results:
        lines.extend(_format_app_result(app_result, verbose=verbose))
        lines.append("")

    lines.append("==========")
    lines.append(f"Scanned apps: {report.summary.scanned_apps}")
    lines.append(f"Found apps: {report.summary.found_apps}")
    lines.append(f"Missing apps: {report.summary.missing_apps}")
    lines.append(f"Skipped apps: {report.summary.skipped_apps}")
    lines.append(f"Error apps: {report.summary.error_apps}")
    lines.append(f"Grand total: {format_bytes(report.summary.grand_total_bytes)}")
    return "\n".join(lines).rstrip()


def _format_app_result(app_result: AppScanResult, verbose: bool) -> list[str]:
    lines: list[str] = [f"==> Scanning {app_result.app_name} storage usage:"]

    if app_result.status == "skipped":
        lines.append(
            f"[INFO ] Skipped: platform mismatch for rule '{app_result.app_id}'."
        )
        for note in app_result.notes:
            lines.append(f"[INFO ] {note}")
        lines.append(f"[TOTAL] {format_bytes(app_result.app_size_bytes)}")
        return lines

    for path_result in app_result.path_results:
        lines.extend(_format_path_result(path_result, verbose=verbose))

    if app_result.status == "missing" and not any(
        item.status == "found" for item in app_result.path_results
    ):
        lines.append("[INFO ] App not found or path does not exist on this machine.")

    for warning in app_result.warnings:
        lines.append(f"[WARN ] {warning}")

    if app_result.user_access_paths:
        for access_path in app_result.user_access_paths:
            lines.append(f"[PATH ] User can access: {access_path}")

    for note in app_result.notes:
        if note == "App not found or no configured paths exist on this machine.":
            continue
        if verbose or "App not found" in note or "skipped" in note.lower():
            lines.append(f"[INFO ] {note}")

    lines.append(f"[TOTAL] {format_bytes(app_result.app_size_bytes)}")
    return lines


def _format_path_result(path_result: PathScanResult, verbose: bool) -> list[str]:
    lines: list[str] = []
    label = f"{path_result.path} ({path_result.category})"

    if path_result.status == "found":
        lines.append(f"[FOUND] {label} .... {format_bytes(path_result.size_bytes)}")
        if path_result.safe_to_clean_hint:
            lines.append(f"[INFO ] Hint: {path_result.safe_to_clean_hint}")
        if path_result.warning:
            lines.append(f"[WARN ] {path_result.warning}")
    elif path_result.status == "miss":
        lines.append(f"[MISS ] {label}")
    elif path_result.status == "error":
        lines.append(f"[WARN ] Failed to scan {label}")
        for note in path_result.notes:
            lines.append(f"[INFO ] {note}")
        if path_result.warning:
            lines.append(f"[WARN ] {path_result.warning}")
    else:
        lines.append(f"[INFO ] {label}")

    if verbose and path_result.status not in {"error"}:
        for note in path_result.notes:
            lines.append(f"[INFO ] {note}")

    return lines
