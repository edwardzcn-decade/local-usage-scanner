from __future__ import annotations

import os
from pathlib import Path


def measure_path_size(path_str: str) -> tuple[int, list[str]]:
    """
    Read-only recursive size calculation.
    """
    notes: list[str] = []
    path = Path(path_str).expanduser()
    try:
        stat_res = path.lstat()  # never follows symlinks
    except PermissionError as exc:
        raise PermissionError(f"Permission denied: {path}") from exc
    except OSError as exc:
        raise OSError(f"Cannot stat path: {path}: {exc}") from exc

    if os.path.islink(path):
        notes.append("Skipped symlink target; symlinks are not followed.")
        return 0, notes
    if path.is_file():
        return stat_res.st_size, notes
    total_size = 0

    def walk_dir(dir: Path) -> None:
        nonlocal total_size
        try:
            with os.scandir(dir) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)
                    try:
                        if entry.is_symlink():
                            notes.append(f"Skipped symlink: {entry_path}")
                            continue
                        if entry.is_file(follow_symlinks=False):
                            total_size += entry.stat(follow_symlinks=False).st_size
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            walk_dir(entry_path)
                            continue
                        notes.append(f"Skipped unsupported file type: {entry_path}")
                    except PermissionError:
                        notes.append(f"Permission denied: {entry_path}")
                    except FileNotFoundError:
                        notes.append(f"Path disappeared during scan: {entry_path}")
                    except OSError as exc:
                        notes.append(f"Scan error at {entry_path}: {exc}")
        except PermissionError as exc:
            # expose to calling layer
            raise PermissionError(f"Permission denied: {dir}") from exc
        except OSError as exc:
            # expose to calling layer
            raise OSError(f"Cannot read directory: {dir}: {exc}") from exc
    walk_dir(path)
    return total_size, notes