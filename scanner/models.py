from dataclasses import dataclass, field


@dataclass
class PathRule:
    path: str
    category: str
    description: str = ""


@dataclass
class AppRule:
    app_id: str
    app_name: str
    platforms: list[str]
    description: str = ""
    paths: list[PathRule] = field(default_factory=list)


@dataclass
class PathScanResult:
    path: str
    status: str
    category: str = ""
    description: str = ""
    size_bytes: int = 0
    notes: list[str] = field(default_factory=list)


@dataclass
class AppScanResult:
    app_id: str
    app_name: str
    status: str
    description: str = ""
    app_size_bytes: int = 0
    path_results: list[PathScanResult] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ScanSummary:
    scanned_apps: int = 0
    found_apps: int = 0
    missing_apps: int = 0
    grand_total_bytes: int = 0


@dataclass
class ScanReport:
    tool_name: str
    app_results: list[AppScanResult] = field(default_factory=list)
    summary: ScanSummary = field(default_factory=ScanSummary)
