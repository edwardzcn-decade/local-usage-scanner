from __future__ import annotations

import platform
import sys


VALID_PLATFORMS = {"macos", "linux", "windows", "wsl"}


def detect_platform() -> str:
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        if "microsoft" in platform.uname().release.lower():
            return "wsl"
        return "linux"
    if sys.platform.startswith(("win32", "cygwin")):
        return "windows"
    return "unknown"


def normalize_platform(value: str) -> str:
    normalized = value.strip().lower()
    aliases = {
        "darwin": "macos",
        "mac": "macos",
        "osx": "macos",
        "ubuntu": "linux",
        "debian": "linux",
        "win": "windows",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in VALID_PLATFORMS:
        raise ValueError(
            f"Unsupported platform override: {value!r}. "
            f"Expected one of: {', '.join(sorted(VALID_PLATFORMS))}"
        )
    return normalized
