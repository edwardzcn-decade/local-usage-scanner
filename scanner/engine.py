from __future__ import annotations

from pathlib import Path
from typing import Callable

from scanner.filesystem import (
    measure_feishu_aha_users,
    measure_path_size,
    measure_telegram_accounts_media,
    measure_wechat_accounts_media,
)
from scanner.models import AppRule, AppScanResult, PathScanResult, ScanReport, PathRule
from scanner.utils import expand_user_path, unique_preserve_order


TELEGRAM_ACCOUNTS_MEDIA_MODE = "telegram_accounts_media"
WECHAT_ACCOUNTS_MEDIA_MODE = "wechat_accounts_media"
FEISHU_AHA_USERS_MODE = "feishu_aha_users"


def _selection_matches(value: str, rules: list[AppRule]) -> bool:
    for rule in rules:
        if (
            value == rule.app_id.lower().strip()
            or value == rule.app_name.lower().strip()
        ):
            return True
    return False


def _scan_app(rule: AppRule, platform_name: str, verbose: bool) -> AppScanResult:
    platform_supported = platform_name in rule.platforms
    result = AppScanResult(
        app_id=rule.app_id,
        app_name=rule.app_name,
        description=rule.description,
        platform_supported=platform_supported,
        status="missing",
        warnings=list(rule.warnings),
        user_access_paths=unique_preserve_order(rule.user_access_paths),
    )

    if not platform_supported:
        result.status = "skipped"
        result.notes.append(
            f"Rule supports {', '.join(rule.platforms)}, skipped on target platform {platform_name}."
        )
        return result

    found_any = False
    encountered_errors = False

    for path_rule in rule.paths:
        path_result = _scan_path(path_rule, verbose=verbose)
        result.path_results.append(path_result)

        if path_result.status == "found":
            found_any = True
            result.matched_paths += 1
            result.app_size_bytes += path_result.size_bytes
        elif path_result.status == "error":
            encountered_errors = True

        if path_result.accessible_path:
            result.user_access_paths.append(path_result.accessible_path)

    result.user_access_paths = unique_preserve_order(result.user_access_paths)

    if found_any:
        result.status = "found"
    elif encountered_errors:
        result.status = "error"
    else:
        result.status = "missing"
        result.notes.append(
            "App not found or no configured paths exist on this machine."
        )

    return result


def _scan_path(path_rule: PathRule, verbose: bool) -> PathScanResult:
    expanded_path = expand_user_path(path_rule.path)
    path_obj = Path(expanded_path)
    result = PathScanResult(
        path=path_rule.path,
        expanded_path=expanded_path,
        category=path_rule.category,
        description=path_rule.description,
        status="miss",
        accessible_path=path_rule.accessible_path,
        safe_to_clean_hint=path_rule.safe_to_clean_hint,
        warning=path_rule.warning,
    )

    if not path_obj.exists():
        result.notes.append("Path does not exist.")
        return result
    try:
        # Add special Telegram mode
        if path_rule.mode == TELEGRAM_ACCOUNTS_MEDIA_MODE:
            tg_media_size_bytes, notes, tg_matched_dirs = (
                measure_telegram_accounts_media(expanded_path)
            )
            if verbose:
                result.notes.extend(notes)
            if tg_matched_dirs == 0:
                result.notes.append("No Telegram account media directories found.")
                return result
            result.size_bytes += tg_media_size_bytes
            result.status = "found"
            result.notes.append(
                f"Matched {tg_matched_dirs} Telegram account media directories."
            )
            return result
        # Add special Wechat mode
        if path_rule.mode == WECHAT_ACCOUNTS_MEDIA_MODE:
            wx_media_size_bytes, notes, wx_matched_dirs = (
                measure_wechat_accounts_media(expanded_path)
            )
            if verbose:
                result.notes.extend(notes)
            if wx_matched_dirs == 0 :
                result.notes.append("No Wechat account directories found.")
                return result
            result.size_bytes += wx_media_size_bytes
            result.status = "found"
            result.notes.append(
                f"Matched {wx_matched_dirs} Wechat account directories."
            )
            return result
        if path_rule.mode == FEISHU_AHA_USERS_MODE:
            aha_size_bytes, notes, matched_entries = measure_feishu_aha_users(
                expanded_path
            )
            if verbose:
                result.notes.extend(notes)
            if not matched_entries:
                result.notes.append("No Feishu aha hash directories found.")
                return result
            result.size_bytes += aha_size_bytes
            result.status = "found"
            result.matched_entries.extend(matched_entries)
            result.notes.append(
                f"Matched {len(matched_entries)} Feishu aha hash directories."
            )
            return result
        size_bytes, notes = measure_path_size(expanded_path)
        result.size_bytes = size_bytes
        result.status = "found"
        if verbose:
            result.notes.extend(notes)
        return result
    except PermissionError as exc:
        result.status = "error"
        result.notes.append(str(exc))
        return result
    except OSError as exc:
        result.status = "error"
        result.notes.append(str(exc))
        return result


def run_scan(
    rules: list[AppRule],
    platform_name: str,
    selected_apps: list[str],
    verbose: bool,
    rules_source: str,
    detected_platform: str,
    on_app_start: Callable[[str, int, int], None] | None = None,
) -> ScanReport:
    normalized_selection = {
        item.strip().lower() for item in selected_apps if item.strip()
    }

    app_results: list[AppScanResult] = []
    global_notes: list[str] = []

    # filter rules with selection
    filter_rules = [
        rule
        for rule in rules
        if not normalized_selection
        or rule.app_id.lower().strip() in normalized_selection
        or rule.app_name.lower().strip() in normalized_selection
    ]

    # unmatched selection
    unmatched_selection = sorted(
        item for item in normalized_selection if not _selection_matches(item, rules)
    )
    for item in unmatched_selection:
        global_notes.append(f"Requested app not found in rules: {item}")

    total_rules = len(filter_rules)
    for index, rule in enumerate(filter_rules, start=1):
        if on_app_start is not None:
            on_app_start(rule.app_name, index, total_rules)
        res = _scan_app(rule, platform_name=platform_name, verbose=verbose)
        app_results.append(res)

    report = ScanReport(
        tool_name="app-storage-scanner",
        tool_mode="read-only scan",
        detected_platform=detected_platform,
        target_platform=platform_name,
        rules_source=rules_source,
        rules_loaded=len(rules),
        selected_apps=selected_apps,
        verbose=verbose,
        app_results=app_results,
        global_notes=global_notes,
    )

    for result in app_results:
        report.summary.scanned_apps += 1
        report.summary.grand_total_bytes += result.app_size_bytes
        if result.status == "found":
            report.summary.found_apps += 1
        elif result.status == "missing":
            report.summary.missing_apps += 1
        elif result.status == "skipped":
            report.summary.skipped_apps += 1
        elif result.status == "error":
            report.summary.error_apps += 1

    return report
