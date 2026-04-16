from scanner.models import ScanReport


def format_bytes(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for u in units:
        if size < 1024 or u == units[-1]:
            if u == "B":
                return f"{int(size)} {u}"
            return f"{size:.2f} {u}"
        size /= 1024
    return f"{size_bytes} B"


def format_scan_text(report: ScanReport) -> str:
    lines = []
    lines.append(f"# {report.tool_name}")
    lines.append("")

    for app in report.app_results:
        lines.append(f"==> {app.app_name} ({app.status})")

        for path_result in app.path_results:
            if path_result.status == "found":
                lines.append(
                    f"[FOUND] {path_result.path} -> {format_bytes(path_result.size_bytes)}"
                )
            else:
                lines.append(f"[MISS ] {path_result.path}")

            for note in path_result.notes:
                lines.append(f"[INFO ] {note}")

        for note in app.notes:
            lines.append(f"[INFO ] {note}")

        lines.append(f"[TOTAL] {format_bytes(app.app_size_bytes)}")
        lines.append("")

    lines.append("==========")
    lines.append(f"Scanned apps: {report.summary.scanned_apps}")
    lines.append(f"Found apps: {report.summary.found_apps}")
    lines.append(f"Missing apps: {report.summary.missing_apps}")
    lines.append(f"Grand total: {format_bytes(report.summary.grand_total_bytes)}")

    return "\n".join(lines)
