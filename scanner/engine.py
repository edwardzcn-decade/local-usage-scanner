from scanner.models import *


def _scan_path(path: str, category: str, description: str) -> PathScanResult:
    # 第2步仍然使用模拟扫描
    fake_sizes = {
        "~/Library/Application Support/Slack/Cache": 120 * 1024 * 1024,
        "~/Library/Logs/Slack": 15 * 1024 * 1024,
        "~/Library/Application Support/Notion/Cache": 80 * 1024 * 1024,
    }

    if path in fake_sizes:
        return PathScanResult(
            path=path,
            status="found",
            category=category,
            description=description,
            size_bytes=fake_sizes[path],
            notes=["这是第2步的模拟扫描结果，下一步会换成真实文件系统扫描。"],
        )

    return PathScanResult(
        path=path,
        status="miss",
        category=category,
        description=description,
        size_bytes=0,
        notes=["模拟结果：当前未命中该路径。"],
    )


def _scan_app(rule: AppRule) -> AppScanResult:
    path_results: list[PathScanResult] = []
    total_size = 0
    flag_found = False
    for path_rule in rule.paths:
        res = _scan_path(path_rule.path, path_rule.category, path_rule.description)
        path_results.append(res)

        if res.status == "found":
            if not flag_found:
                flag_found = True
            total_size += res.size_bytes
    return AppScanResult(
        app_id=rule.app_id,
        app_name=rule.app_name,
        status="found" if flag_found else "missing",
        description=rule.description,
        app_size_bytes=total_size,
        path_results=path_results,
    )


def run_scan(rules: list[AppRule]) -> ScanReport:
    # use fake data
    app_results: list[AppScanResult] = []
    for rule in rules:
        res = _scan_app(rule)
        app_results.append(res)

    summ = ScanSummary()
    for app in app_results:
        summ.scanned_apps += 1
        summ.grand_total_bytes += app.app_size_bytes
        if app.status == "found":
            summ.found_apps += 1
        else:
            summ.missing_apps += 1

    return ScanReport(
        tool_name="local-usage-scanner-v0.1.0",
        app_results=app_results,
        summary=summ,
    )

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
