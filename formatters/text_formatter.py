from __future__ import annotations

import os
import sys

from scanner.models import AppScanResult, PathScanResult, ScanReport
from scanner.utils import format_bytes


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

COLOR_BLUE = "\033[34m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_MAGENTA = "\033[35m"
COLOR_WHITE = "\033[37m"


def format_scan_text(
    report: ScanReport,
    verbose: bool = False,
    use_color: bool | None = None,
    compact: bool = False,
) -> str:
    resolved_use_color = _should_use_color() if use_color is None else use_color
    lines: list[str] = []

    lines.append(
        _style(
            (
                f"app-storage-scanner  {DIM if resolved_use_color else ''}"
                f"({report.tool_mode}, detected={report.detected_platform}, target={report.target_platform})"
            ),
            BOLD,
            resolved_use_color,
            reset=False,
        )
        + (RESET if resolved_use_color else "")
    )
    lines.append("")
    lines.append(_format_summary(report, use_color=resolved_use_color))
    lines.append("")

    if report.global_notes:
        for note in report.global_notes:
            lines.append(_tagged("INFO", note, COLOR_CYAN, resolved_use_color))
        lines.append("")

    app_results = sorted(
        report.app_results,
        key=lambda item: (item.app_size_bytes, item.app_name.lower()),
        reverse=True,
    )

    for index, app_result in enumerate(app_results, start=1):
        lines.extend(
            _format_app_result(
                app_result,
                rank=index,
                grand_total=report.summary.grand_total_bytes,
                verbose=verbose,
                use_color=resolved_use_color,
                compact=compact,
            )
        )
        lines.append("")

    return "\n".join(lines).rstrip()


def _format_app_result(
    app_result: AppScanResult,
    rank: int,
    grand_total: int,
    verbose: bool,
    use_color: bool,
    compact: bool,
) -> list[str]:
    total = format_bytes(app_result.app_size_bytes)
    bar = _size_bar(app_result.app_size_bytes, grand_total, use_color)
    status_label = _status_text(app_result.status, use_color)
    lines: list[str] = [
        (
            f"{_style(f'{rank:>2}.', DIM, use_color)} "
            f"{_style(app_result.app_name, BOLD, use_color)}  "
            f"{status_label}  "
            f"{_style(total, COLOR_MAGENTA, use_color)}"
            f"{('  ' + bar) if bar else ''}"
        )
    ]

    if app_result.status == "skipped":
        lines.append(
            _tagged(
                "INFO",
                f"Skipped: platform mismatch for rule '{app_result.app_id}'.",
                COLOR_CYAN,
                use_color,
            )
        )
        for note in app_result.notes:
            lines.append(_tagged("INFO", note, COLOR_CYAN, use_color))
        return lines

    for path_result in app_result.path_results:
        lines.extend(
            _format_path_result(
                path_result,
                verbose=verbose,
                use_color=use_color,
                compact=compact,
            )
        )

    if app_result.status == "missing" and not any(
        item.status == "found" for item in app_result.path_results
    ):
        lines.append(_tagged("INFO", "App not found or path does not exist on this machine.", COLOR_CYAN, use_color))

    for warning in app_result.warnings:
        lines.append(_tagged("WARN", warning, COLOR_YELLOW, use_color))

    if app_result.user_access_paths and not compact:
        for access_path in app_result.user_access_paths:
            lines.append(
                _tagged("PATH", f"User can access: {access_path}", COLOR_BLUE, use_color)
            )

    for note in app_result.notes:
        if note == "App not found or no configured paths exist on this machine.":
            continue
        if verbose or "App not found" in note or "skipped" in note.lower():
            lines.append(_tagged("INFO", note, COLOR_CYAN, use_color))

    return lines


def _format_path_result(
    path_result: PathScanResult,
    verbose: bool,
    use_color: bool,
    compact: bool,
) -> list[str]:
    lines: list[str] = []
    label = path_result.path
    category_label = _style(path_result.category, COLOR_WHITE, use_color)

    if path_result.status == "found":
        lines.append(
            _tagged(
                "FOUND",
                f"{category_label}  {format_bytes(path_result.size_bytes)}",
                COLOR_GREEN,
                use_color,
            )
        )
        lines.append(_indent(label, level=1))
        if path_result.safe_to_clean_hint:
            lines.append(
                _tagged(
                    "HINT",
                    path_result.safe_to_clean_hint,
                    COLOR_CYAN,
                    use_color,
                )
            )
        if path_result.warning:
            lines.append(_tagged("WARN", path_result.warning, COLOR_YELLOW, use_color))
        for matched_entry in path_result.matched_entries:
            lines.append(
                _indent(
                    _tagged(
                        "ITEM",
                        f"{matched_entry.label}  {format_bytes(matched_entry.size_bytes)}",
                        COLOR_MAGENTA,
                        use_color,
                    ),
                    level=1,
                )
            )
            if matched_entry.warning and not compact:
                lines.append(
                    _indent(
                        _tagged("INFO", matched_entry.warning, COLOR_CYAN, use_color),
                        level=2,
                    )
                )
    elif path_result.status == "miss":
        if not compact:
            lines.append(
                _tagged("MISS", f"{category_label}  {label}", COLOR_BLUE, use_color)
            )
    elif path_result.status == "error":
        lines.append(
            _tagged("WARN", f"Failed to scan {category_label}  {label}", COLOR_RED, use_color)
        )
        for note in path_result.notes:
            lines.append(_tagged("INFO", note, COLOR_CYAN, use_color))
        if path_result.warning:
            lines.append(_tagged("WARN", path_result.warning, COLOR_YELLOW, use_color))
    else:
        if not compact:
            lines.append(_tagged("INFO", f"{category_label}  {label}", COLOR_CYAN, use_color))

    if verbose:
        lines.append(
            _indent(
                _tagged("PATH", path_result.expanded_path, COLOR_BLUE, use_color),
                level=1,
            )
        )

    if verbose and path_result.status not in {"error"}:
        for note in path_result.notes:
            lines.append(
                _indent(
                    _tagged("INFO", note, COLOR_CYAN, use_color),
                    level=1,
                )
            )

    return lines


def _format_summary(report: ScanReport, use_color: bool) -> str:
    parts = [
        _style("Summary", BOLD, use_color),
        f"scanned={report.summary.scanned_apps}",
        f"found={report.summary.found_apps}",
        f"missing={report.summary.missing_apps}",
        f"skipped={report.summary.skipped_apps}",
        f"errors={report.summary.error_apps}",
        f"total={format_bytes(report.summary.grand_total_bytes)}",
    ]
    return "  ".join(parts)


def _status_text(status: str, use_color: bool) -> str:
    status_map = {
        "found": ("FOUND", COLOR_GREEN),
        "missing": ("MISSING", COLOR_BLUE),
        "skipped": ("SKIPPED", COLOR_CYAN),
        "error": ("ERROR", COLOR_RED),
    }
    label, color = status_map.get(status, (status.upper(), COLOR_WHITE))
    return _style(label, color, use_color)


def _tagged(tag: str, message: str, color: str, use_color: bool) -> str:
    return f"{_style(f'[{tag}]', color, use_color)} {message}"


def _size_bar(size_bytes: int, grand_total: int, use_color: bool) -> str:
    if grand_total <= 0 or size_bytes <= 0:
        return ""
    width = 18
    filled = max(1, round((size_bytes / grand_total) * width))
    filled = min(width, filled)
    bar = "■" * filled + "·" * (width - filled)
    return _style(bar, COLOR_MAGENTA, use_color)


def _style(text: str, color: str, use_color: bool, reset: bool = True) -> str:
    if not use_color:
        return text
    suffix = RESET if reset else ""
    return f"{color}{text}{suffix}"


def _should_use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if os.name != "nt":
        return True
    return any(
        os.environ.get(key)
        for key in ("WT_SESSION", "ANSICON", "ConEmuANSI", "TERM_PROGRAM")
    ) or os.environ.get("TERM", "").lower() == "xterm"


def _indent(text: str, level: int = 1) -> str:
    return f"{'  ' * level}{text}"
