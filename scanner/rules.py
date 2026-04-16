from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scanner.models import AppRule, PathRule
from scanner.utils import unique_preserve_order


@dataclass
class RuleLoadResult:
    rules: list[AppRule]
    notes: list[str]


def _discover_rule_files(src: Path) -> list[Path]:
    if not src.exists():
        raise RuntimeError(f"Rules source path does not exist: {src}")
    if src.is_file():
        return [src]
    rule_files = sorted(p for p in src.glob("*.json") if p.is_file())
    if not rule_files:
        raise RuntimeError(f"No JSON rule files found in rules source directory: {src}")
    return rule_files


# def load_rules(rule_file: str) -> list[AppRule]:
def load_rules(rules_src: Path) -> RuleLoadResult:
    rule_files = _discover_rule_files(rules_src)
    loaded: list[AppRule] = []
    notes: list[str] = []

    for rule_file in rule_files:
        try:
            data = json.loads(rule_file.read_text(encoding="utf-8"))
        except OSError as exc:
            notes.append(f"Skipped rules file {rule_file}.")
            notes.append(f"OS read error: {exc}")
            continue
        except json.JSONDecodeError as exc:
            notes.append(f"Skipped rules file {rule_file}.")
            notes.append(f"Invalid JSON. Decode error: {exc}")
            continue
        if isinstance(data, dict):
            apps = data.get("apps", [])
        elif isinstance(data, list):
            apps = data
        else:
            notes.append(
                f"Skipped rules file {rule_file}."
                f'Top-level JSON must be an object with "apps" or a list.'
            )
            continue
        for index, app_config in enumerate(apps):
            try:
                loaded.append(_parse_app_rule(app_config))
            except ValueError as exc:
                notes.append(
                    f"Skipped invalid app rule in {rule_file} app[{index}]: {exc}"
                )
    return RuleLoadResult(rules=loaded, notes=notes)


def _require_string(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid string field: {key}")
    return value.strip()


def _optional_string(data: dict, key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Field {key!r} must be a non-empty string when provided")
    return value.strip()


def _parse_app_rule(data: dict) -> AppRule:
    # rules: list[AppRule] = []
    if not isinstance(data, dict):
        raise ValueError("Each app rule must be a JSON object")
    app_id = _require_string(data, "id")
    app_name = _require_string(data, "name")
    platforms = data.get("platforms")
    if not isinstance(platforms, list) or not platforms:
        raise ValueError("platforms must be a non-empty string list")
    description = data.get("description", "").strip()
    user_access_paths = data.get("user_access_paths", [])
    warnings = data.get("warnings", [])
    path_rules_data = data.get("paths", [])

    path_rules: list[PathRule] = []
    for index, path_data in enumerate(path_rules_data):
        if not isinstance(path_data, dict):
            raise ValueError(f"paths[{index}] must be a non-empty string list")

        path_rules.append(
            PathRule(
                path=_require_string(path_data, "path"),
                category=_require_string(path_data, "category"),
                description=path_data.get("description", ""),
                accessible_path=_optional_string(path_data, "accessible_path"),
                safe_to_clean_hint=_optional_string(path_data, "safe_to_clean_hint"),
                warning=_optional_string(path_data, "warning"),
            )
        )

    return AppRule(
        app_id=app_id,
        app_name=app_name,
        platforms=unique_preserve_order([item.strip().lower() for item in platforms]),
        description=description,
        # user_access_paths=unique_preserve_order(user_access_paths)
        user_access_paths=user_access_paths,
        warnings=warnings,
        paths=path_rules,
    )
