from scanner.models import *


def run_scan() -> ScanReport:
    # use fake data
    slack_cache = PathScanResult(
        path="~/Library/Application Support/Slack/Cache",
        status="found",
        size_bytes=120 * 1024 * 1024,
        notes=["This is a fake example for Slack"],
    )
    slack_logs = PathScanResult(
        path="~/Library/Logs/Slack",
        status="found",
        size_bytes=15 * 1024 * 1024,
    )
    slack_result = AppScanResult(
        app_id="slack",
        app_name="Slack",
        status="found",
        app_size_bytes=slack_cache.size_bytes + slack_logs.size_bytes,
        path_results=[slack_cache, slack_logs],
        notes=["Slack scan result"],
    )
    notion_result = AppScanResult(
        app_id="notion",
        app_name="Notion",
        status="missing",
        app_size_bytes=0,
        path_results=[
            PathScanResult(
                path="~/Library/Application Support/Notion/Cache",
                status="miss",
                size_bytes=0,
                notes=["Cant find notion cache"],
            )
        ],
        notes=["Notion scan result"],
    )
    summ = ScanSummary(
        scanned_apps=2,
        found_apps=1,
        missing_apps=1,
        grand_total_bytes=slack_result.app_size_bytes + notion_result.app_size_bytes,
    )
    return ScanReport(
        tool_name="local-usage-scanner-v0.1.0",
        app_results=[slack_result, notion_result],
        summary=summ,
    )
