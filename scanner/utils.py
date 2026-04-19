from __future__ import annotations

import os
import re
from pathlib import Path


WINDOWS_ENV_VAR_PATTERN = re.compile(r"%([^%]+)%")


def expand_user_path(path_str: str, env: dict[str, str] | None = None) -> str:
    env_vars = env if env is not None else os.environ

    def replace_var(match: re.Match[str]) -> str:
        key = match.group(1)
        return env_vars.get(key, match.group(0))

    expanded = WINDOWS_ENV_VAR_PATTERN.sub(replace_var, path_str)
    return str(Path(expanded).expanduser())


def format_bytes(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for u in units:
        if size < 1024 or u == units[-1]:
            if u == "B":
                return f"{int(size)} {u}"
            number = f"{size:.2f}".rstrip("0").rstrip(".")
            return f"{number} {u}"
        size /= 1024
    return f"{size_bytes} B"


def unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = os.path.normcase(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result
