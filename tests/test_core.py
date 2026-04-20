from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from formatters.text_formatter import format_scan_text
from main import build_parser, get_default_rules_path
from scanner.filesystem import measure_feishu_aha_users
from scanner.models import AppScanResult, MatchedEntry, PathScanResult, ScanReport
from scanner.utils import expand_user_path


class ParserTests(unittest.TestCase):
    def test_default_format_is_text(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.format, "text")

    def test_text_and_json_formats_remain_available(self) -> None:
        parser = build_parser()
        self.assertEqual(parser.parse_args(["--format", "text"]).format, "text")
        self.assertEqual(parser.parse_args(["--format", "json"]).format, "json")

    def test_optional_text_flags_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--no-color", "--progress", "--compact"])
        self.assertTrue(args.no_color)
        self.assertTrue(args.progress)
        self.assertTrue(args.compact)


class RulesPathTests(unittest.TestCase):
    def test_default_rules_path_is_platform_specific(self) -> None:
        self.assertTrue(
            str(get_default_rules_path("macos")).endswith("default_macos_apps_max.json")
        )
        self.assertTrue(
            str(get_default_rules_path("windows")).endswith("default_windows_apps.json")
        )
        self.assertTrue(
            str(get_default_rules_path("linux")).endswith("default_linux_apps.json")
        )


class ExpandUserPathTests(unittest.TestCase):
    def test_expand_user_path_supports_windows_env_vars(self) -> None:
        expanded = expand_user_path(
            r"%APPDATA%/LarkShell/aha/users",
            env={"APPDATA": r"C:\Users\demo\AppData\Roaming"},
        )
        self.assertEqual(
            expanded,
            str(Path(r"C:\Users\demo\AppData\Roaming/LarkShell/aha/users")),
        )

    def test_expand_user_path_supports_localappdata_and_userprofile(self) -> None:
        localappdata = expand_user_path(
            r"%LOCALAPPDATA%/Programs/Feishu",
            env={"LOCALAPPDATA": r"C:\Users\demo\AppData\Local"},
        )
        userprofile = expand_user_path(
            r"%USERPROFILE%/Documents/Lightroom",
            env={"USERPROFILE": r"C:\Users\demo"},
        )
        self.assertEqual(
            localappdata,
            str(Path(r"C:\Users\demo\AppData\Local/Programs/Feishu")),
        )
        self.assertEqual(
            userprofile,
            str(Path(r"C:\Users\demo/Documents/Lightroom")),
        )


class FeishuAhaUsersTests(unittest.TestCase):
    def test_measure_feishu_aha_users_only_counts_hash_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            hash_one = root / "0123456789abcdef"
            hash_two = root / "abcdef0123456789abcdef0123456789"
            ignored = root / "global"
            hash_one.mkdir()
            hash_two.mkdir()
            ignored.mkdir()

            (hash_one / "a.bin").write_bytes(b"a" * 10)
            (hash_two / "b.bin").write_bytes(b"b" * 20)
            (ignored / "c.bin").write_bytes(b"c" * 99)

            total_size, notes, matched_entries = measure_feishu_aha_users(str(root))

        self.assertEqual(total_size, 30)
        self.assertEqual([item.label for item in matched_entries], [hash_two.name, hash_one.name])
        self.assertEqual([item.size_bytes for item in matched_entries], [20, 10])
        self.assertTrue(any("Feishu aha user" in note for note in notes))


class TextFormatterTests(unittest.TestCase):
    def _build_report(self) -> ScanReport:
        return ScanReport(
            tool_name="app-storage-scanner",
            tool_mode="read-only scan",
            detected_platform="windows",
            target_platform="windows",
            rules_source="rules/default_windows_apps.json",
            rules_loaded=1,
            selected_apps=["feishu"],
            verbose=False,
            app_results=[
                AppScanResult(
                    app_id="feishu",
                    app_name="Feishu",
                    description="Feishu test report.",
                    platform_supported=True,
                    status="found",
                    app_size_bytes=300,
                    matched_paths=1,
                    path_results=[
                        PathScanResult(
                            path=r"%APPDATA%/Feishu/aha/users",
                            expanded_path=r"C:\Users\demo\AppData\Roaming\Feishu\aha\users",
                            category="delete-candidates",
                            description="Hash directories.",
                            status="found",
                            size_bytes=300,
                            matched_entries=[
                                MatchedEntry(
                                    label="abcdef0123456789",
                                    path=r"C:\Users\demo\AppData\Roaming\Feishu\aha\users\abcdef0123456789",
                                    size_bytes=300,
                                    warning="Delete candidate only; scanner remains read-only.",
                                )
                            ],
                            notes=["Matched 1 Feishu aha hash directories."],
                        ),
                        PathScanResult(
                            path=r"%APPDATA%/Feishu/sdk_storage/log",
                            expanded_path=r"C:\Users\demo\AppData\Roaming\Feishu\sdk_storage\log",
                            category="logs",
                            description="Logs.",
                            status="miss",
                            notes=["Path does not exist."],
                        ),
                    ],
                    user_access_paths=[r"%APPDATA%/Feishu/aha/users"],
                    warnings=["Read-only only."],
                )
            ],
        )

    def test_no_color_output_has_no_ansi_sequences(self) -> None:
        output = format_scan_text(self._build_report(), use_color=False)
        self.assertNotIn("\033[", output)

    def test_compact_hides_miss_and_access_paths(self) -> None:
        output = format_scan_text(self._build_report(), use_color=False, compact=True)
        self.assertIn("[FOUND]", output)
        self.assertIn("[ITEM]", output)
        self.assertNotIn("[MISS]", output)
        self.assertNotIn("[PATH] User can access", output)

    def test_verbose_shows_expanded_path(self) -> None:
        output = format_scan_text(self._build_report(), use_color=False, verbose=True)
        self.assertIn(r"C:\Users\demo\AppData\Roaming\Feishu\aha\users", output)


if __name__ == "__main__":
    unittest.main()
