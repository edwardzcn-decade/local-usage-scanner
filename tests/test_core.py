from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from main import build_parser, get_default_rules_path
from scanner.filesystem import measure_feishu_aha_users
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


if __name__ == "__main__":
    unittest.main()
