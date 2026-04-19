from __future__ import annotations

import os
import re
from pathlib import Path

from scanner.models import MatchedEntry
from scanner.utils import format_bytes


FEISHU_HASH_DIR_PATTERN = re.compile(r"^[0-9a-f]{16,}$")


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


def measure_telegram_accounts_media(tg_stable: str) -> tuple[int, list[str], int]:
    """
    Scan only Telegram stable/*/postbox/media directories.
    Returns:
        total_size_bytes, notes, matched_media_directories
    """
    notes: list[str] = []
    tg_stable_dir = Path(tg_stable).expanduser()

    try:
        stat_res = tg_stable_dir.lstat()
    except PermissionError as exc:
        raise PermissionError(f"Permission denied: {tg_stable_dir}") from exc
    except OSError as exc:
        raise OSError(f"Cannot stat path: {tg_stable_dir}: {exc}") from exc

    if os.path.islink(tg_stable_dir):
        notes.append("Skipped symlink target; symlinks are not followed.")
        return 0, notes, 0

    if not tg_stable_dir.is_dir():
        raise OSError(f"Telegram stable root is not a directory: {tg_stable_dir}")
    total_size = 0
    matched = 0

    try:
        with os.scandir(tg_stable_dir) as entries:
            for entry in entries:
                account_root = Path(entry.path)
                try:
                    if entry.is_symlink():
                        notes.append(
                            f"Skipped symlink account directory: {account_root}"
                        )
                        continue
                    if not entry.is_dir(follow_symlinks=False):
                        continue

                    media_dir = account_root / "postbox" / "media"
                    if not media_dir.exists():
                        # TODO just ignore temp,accounts-metadata,Library,Wallpapers and logs
                        # notes.append(
                        #     f"No media directory for account root: {account_root.name}"
                        # )
                        continue

                    size_bytes, sub_notes = measure_path_size(str(media_dir))
                    matched += 1
                    total_size += size_bytes
                    notes.append(
                        f"Telegram account {account_root.name}: postbox/media -> {format_bytes(size_bytes)} bytes"
                    )
                    notes.extend(sub_notes)

                except PermissionError:
                    notes.append(f"Permission denied: {account_root}")
                except FileNotFoundError:
                    notes.append(f"Path disappeared during scan: {account_root}")
                except OSError as exc:
                    notes.append(f"Scan error at {account_root}: {exc}")

    except PermissionError as exc:
        raise PermissionError(f"Permission denied: {tg_stable_dir}") from exc
    except OSError as exc:
        raise OSError(f"Cannot read directory: {tg_stable_dir}: {exc}") from exc

    if matched == 0:
        notes.append("No Telegram account media directories found under stable root.")

    return total_size, notes, matched


def measure_wechat_accounts_media(wx_files: str) -> tuple[int, list[str], int]:
    """
    Scan only Wechat/Weixin account roots and common media/cache directories (not include chat history).
    Supported layouts:
    1) ~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/<account>/
    2) ~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/<account>/

    Returns:
        total_size_bytes, notes, matched_account_dirs
    """
    notes: list[str] = []
    wx_files_dir = Path(wx_files).expanduser()

    try:
        wx_files_dir.lstat()
    except PermissionError as exc:
        raise PermissionError(f"Permission denied: {wx_files_dir}") from exc
    except OSError as exc:
        raise OSError(f"Cannot stat path: {wx_files_dir}: {exc}") from exc

    if os.path.islink(wx_files_dir):
        notes.append("Skipped symlink target; symlinks are not followed.")
        return 0, notes, 0

    if not wx_files_dir.is_dir():
        raise OSError(f"WeChat files root is not a directory: {wx_files_dir}")

    total_size = 0
    matched_accounts = 0

    # Generally safe to delete sudirs files
    candidate_subdirs = [
        "Cache",
        "predownload",
        "mmxpt",
        "Files",
        "Video",
        "Favorites",
        "Message/MessageTemp",
        "msg/attach",
        "msg/file",
        "msg/video",
    ]

    # FIXME include dir with longer name but not starts with 'wxid_'
    #       is not safe
    def looks_like_account_dir(name: str) -> bool:
        return name.startswith("wxid_") or len(name) >= 16

    try:
        with os.scandir(wx_files_dir) as entries:
            for entry in entries:
                account_root = Path(entry.path)
                try:
                    if entry.is_symlink():
                        notes.append(
                            f"Skipped symlink account directory: {account_root}"
                        )
                        continue
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    if not looks_like_account_dir(account_root.name):
                        continue

                    matched_this_account = False
                    account_total = 0

                    for rel in candidate_subdirs:
                        candidate = account_root / rel
                        if candidate.exists():
                            size_bytes, sub_notes = measure_path_size(str(candidate))
                            account_total += size_bytes
                            notes.append(
                                f"WeChat account {account_root.name}: {rel} -> {size_bytes} bytes"
                            )
                            notes.extend(sub_notes)
                            matched_this_account = True

                    if matched_this_account:
                        matched_accounts += 1
                        total_size += account_total
                    else:
                        notes.append(
                            f"WeChat account {account_root.name}: no known media/cache directories found"
                        )

                except PermissionError:
                    notes.append(f"Permission denied: {account_root}")
                except FileNotFoundError:
                    notes.append(f"Path disappeared during scan: {account_root}")
                except OSError as exc:
                    notes.append(f"Scan error at {account_root}: {exc}")

    except PermissionError as exc:
        raise PermissionError(f"Permission denied: {wx_files_dir}") from exc
    except OSError as exc:
        raise OSError(f"Cannot read directory: {wx_files_dir}: {exc}") from exc

    if matched_accounts == 0:
        notes.append("No WeChat account media directories found under root.")

    return total_size, notes, matched_accounts


def measure_feishu_aha_users(aha_users_root: str) -> tuple[int, list[str], list[MatchedEntry]]:
    """
    Scan Feishu aha/users and sum only hash-named directories.

    Returns:
        total_size_bytes, notes, matched_entries
    """
    notes: list[str] = []
    matched_entries: list[MatchedEntry] = []
    root_dir = Path(aha_users_root).expanduser()

    try:
        root_dir.lstat()
    except PermissionError as exc:
        raise PermissionError(f"Permission denied: {root_dir}") from exc
    except OSError as exc:
        raise OSError(f"Cannot stat path: {root_dir}: {exc}") from exc

    if os.path.islink(root_dir):
        notes.append("Skipped symlink target; symlinks are not followed.")
        return 0, notes, matched_entries

    if not root_dir.is_dir():
        raise OSError(f"Feishu aha users root is not a directory: {root_dir}")

    total_size = 0

    try:
        with os.scandir(root_dir) as entries:
            for entry in entries:
                entry_path = Path(entry.path)
                try:
                    if entry.is_symlink():
                        notes.append(f"Skipped symlink directory: {entry_path}")
                        continue
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    if not FEISHU_HASH_DIR_PATTERN.fullmatch(entry.name):
                        continue

                    size_bytes, sub_notes = measure_path_size(str(entry_path))
                    total_size += size_bytes
                    matched_entries.append(
                        MatchedEntry(
                            label=entry.name,
                            path=str(entry_path),
                            size_bytes=size_bytes,
                            warning="Delete candidate only; scanner remains read-only.",
                        )
                    )
                    notes.append(
                        f"Feishu aha user {entry.name} -> {format_bytes(size_bytes)}"
                    )
                    notes.extend(sub_notes)
                except PermissionError:
                    notes.append(f"Permission denied: {entry_path}")
                except FileNotFoundError:
                    notes.append(f"Path disappeared during scan: {entry_path}")
                except OSError as exc:
                    notes.append(f"Scan error at {entry_path}: {exc}")
    except PermissionError as exc:
        raise PermissionError(f"Permission denied: {root_dir}") from exc
    except OSError as exc:
        raise OSError(f"Cannot read directory: {root_dir}: {exc}") from exc

    matched_entries.sort(key=lambda item: item.size_bytes, reverse=True)

    if not matched_entries:
        notes.append("No Feishu aha hash directories found under users root.")

    return total_size, notes, matched_entries
