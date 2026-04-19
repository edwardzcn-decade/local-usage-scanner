from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class MatchedEntry:
    label: str
    path: str
    size_bytes: int
    warning: str | None = None


@dataclass
class PathRule:
    path: str
    category: str
    description: str = ""
    accessible_path: str | None = None
    safe_to_clean_hint: str | None = None
    warning: str | None = None
    mode: str | None = None


@dataclass
class AppRule:
    app_id: str
    app_name: str
    platforms: list[str]
    description: str = ""
    user_access_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    paths: list[PathRule] = field(default_factory=list)


@dataclass
class PathScanResult:
    path: str
    expanded_path: str
    category: str
    description: str
    status: str
    size_bytes: int = 0
    accessible_path: str | None = None
    safe_to_clean_hint: str | None = None
    warning: str | None = None
    matched_entries: list[MatchedEntry] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class AppScanResult:
    app_id: str
    app_name: str
    description: str
    platform_supported: bool
    status: str
    app_size_bytes: int = 0
    matched_paths: int = 0
    path_results: list[PathScanResult] = field(default_factory=list)
    user_access_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ScanSummary:
    scanned_apps: int = 0
    found_apps: int = 0
    missing_apps: int = 0
    skipped_apps: int = 0
    error_apps: int = 0
    grand_total_bytes: int = 0


@dataclass
class ScanReport:
    tool_name: str
    tool_mode: str
    detected_platform: str
    target_platform: str
    rules_source: str
    rules_loaded: int
    selected_apps: list[str]
    verbose: bool
    app_results: list[AppScanResult] = field(default_factory=list)
    global_notes: list[str] = field(default_factory=list)
    summary: ScanSummary = field(default_factory=ScanSummary)

    def to_dict(self) -> dict:
        return asdict(self)
