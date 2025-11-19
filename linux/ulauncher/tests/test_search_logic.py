from __future__ import annotations

import os
import stat
import sys
import tempfile
import unittest
from datetime import datetime
from typing import cast
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath("linux/ulauncher"))

from src.search import (  # pyright: ignore[reportImplicitRelativeImport]
    score_path,
    categorize_path,
    format_file_size,
    categorize_and_sort,
    search_plocate,
)
from src.models import (  # pyright: ignore[reportImplicitRelativeImport]
    FrequencyData,
    FrequencyEntry,
)
from src.constants import (  # pyright: ignore[reportImplicitRelativeImport]
    ICON_DIRECTORY,
    ICON_FILE,
    ICON_OPEN,
)


class TestSearchUnit(unittest.TestCase):
    def test_score_path_hidden_files_have_higher_penalty(self):
        # Arrange
        hidden_path = "/home/user/.hidden/file.txt"
        normal_path = "/home/user/normal/file.txt"
        frequency = FrequencyData()
        half_life_days = 7.0

        # Act
        hidden_score = score_path(hidden_path, frequency, half_life_days)
        normal_score = score_path(normal_path, frequency, half_life_days)

        # Assert
        self.assertGreater(hidden_score, normal_score)

    def test_score_path_deeper_paths_have_higher_penalty(self):
        # Arrange
        shallow_path = "/home/file.txt"
        deep_path = "/home/user/documents/work/project/file.txt"
        frequency = FrequencyData()
        half_life_days = 7.0

        # Act
        shallow_score = score_path(shallow_path, frequency, half_life_days)
        deep_score = score_path(deep_path, frequency, half_life_days)

        # Assert
        self.assertLess(shallow_score, deep_score)

    def test_score_path_frequent_paths_have_lower_score(self):
        # Arrange
        path = "/home/user/frequent.txt"
        frequency = FrequencyData(
            entries={
                path: FrequencyEntry(
                    count=100, last_accessed=datetime.now().isoformat()
                )
            }
        )
        frequency_empty = FrequencyData()
        half_life_days = 7.0

        # Act
        score_with_freq = score_path(path, frequency, half_life_days)
        score_without_freq = score_path(path, frequency_empty, half_life_days)

        # Assert
        self.assertLess(score_with_freq, score_without_freq)

    @patch("src.search.os.stat")
    def test_categorize_and_sort_prioritizes_directories_over_files(
        self, mock_stat: MagicMock
    ):
        # Arrange
        paths = ["/home/file.txt", "/home/deep/nested/folder"]
        frequency = FrequencyData()
        half_life_days = 7.0

        def stat_side_effect(path: str) -> MagicMock:
            stat_result = MagicMock()
            stat_result.st_size = 1024
            if "folder" in path:
                stat_result.st_mode = stat.S_IFDIR
            else:
                stat_result.st_mode = stat.S_IFREG
            return stat_result

        mock_stat.side_effect = stat_side_effect

        # Act
        results = categorize_and_sort(paths, frequency, half_life_days)

        # Assert
        self.assertEqual(results[0][0], "/home/deep/nested/folder")
        self.assertEqual(results[1][0], "/home/file.txt")

    @patch("src.search.os.stat")
    def test_categorize_and_sort_secondary_sort_is_score(self, mock_stat: MagicMock):
        # Arrange
        paths = ["/long/path/to/file.txt", "/short/file.txt"]
        frequency = FrequencyData()
        half_life_days = 7.0

        stat_result = MagicMock()
        stat_result.st_mode = stat.S_IFREG
        stat_result.st_size = 1024
        mock_stat.return_value = stat_result

        # Act
        results = categorize_and_sort(paths, frequency, half_life_days)

        # Assert
        self.assertEqual(results[0][0], "/short/file.txt")
        self.assertEqual(results[1][0], "/long/path/to/file.txt")

    @patch("src.search.subprocess.check_output")
    def test_search_plocate_escapes_special_regex_characters(
        self, mock_subprocess: MagicMock
    ):
        # Arrange
        risky_query = "file (1) [test]"

        # Act
        _ = search_plocate(risky_query)

        # Assert
        call_args = mock_subprocess.call_args
        cmd_list = cast("list[str]", call_args[0][0])
        cmd_str = " ".join(cmd_list)

        self.assertIn("--regexp", cmd_list)
        self.assertIn(r"\(1\)", cmd_str)
        self.assertIn(r"\[test\]", cmd_str)

    @patch("src.search.subprocess.check_output")
    def test_search_plocate_handles_shell_injection_attempts(
        self, mock_subprocess: MagicMock
    ):
        # Arrange
        malicious_query = "; rm -rf /"

        # Act
        _ = search_plocate(malicious_query)

        # Assert
        call_args = mock_subprocess.call_args
        cmd_list = cast("list[str]", call_args[0][0])
        cmd_str = " ".join(cmd_list)

        self.assertIsInstance(cmd_list, list)
        self.assertIn(r"\-rf", cmd_str)

    def test_format_file_size_zero_bytes(self):
        # Arrange
        size = 0

        # Act
        result = format_file_size(size)

        # Assert
        self.assertEqual(result, "0 B")

    def test_format_file_size_bytes_formats_correctly(self):
        # Arrange
        size = 500

        # Act
        result = format_file_size(size)

        # Assert
        self.assertEqual(result, "500 B")

    def test_format_file_size_kilobytes_formats_correctly(self):
        # Arrange
        size_1kb = 1024
        size_2kb = 2048
        size_boundary = 1023 * 1024

        # Act
        result_1kb = format_file_size(size_1kb)
        result_2kb = format_file_size(size_2kb)
        result_boundary = format_file_size(size_boundary)

        # Assert
        self.assertEqual(result_1kb, "1.0 KB")
        self.assertEqual(result_2kb, "2.0 KB")
        self.assertEqual(result_boundary, "1023.0 KB")

    def test_format_file_size_megabytes_formats_correctly(self):
        # Arrange
        size_1mb = 1024 * 1024
        size_5mb = 5 * 1024 * 1024

        # Act
        result_1mb = format_file_size(size_1mb)
        result_5mb = format_file_size(size_5mb)

        # Assert
        self.assertEqual(result_1mb, "1.0 MB")
        self.assertEqual(result_5mb, "5.0 MB")

    def test_format_file_size_gigabytes_formats_correctly(self):
        # Arrange
        size_1gb = 1024 * 1024 * 1024
        size_3gb = 3 * 1024 * 1024 * 1024

        # Act
        result_1gb = format_file_size(size_1gb)
        result_3gb = format_file_size(size_3gb)

        # Assert
        self.assertEqual(result_1gb, "1.0 GB")
        self.assertEqual(result_3gb, "3.0 GB")

    def test_categorize_path_directory_returns_directory_icon(self):
        # Arrange
        temp_dir = tempfile.mkdtemp()

        # Act
        result = categorize_path(temp_dir)

        # Assert
        self.assertEqual(result[0], temp_dir)
        self.assertEqual(result[1], ICON_DIRECTORY)

        os.rmdir(temp_dir)

    def test_categorize_path_file_returns_file_icon_with_size(self):
        # Arrange
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        _ = temp_file.write(b"test content")
        temp_file.close()

        # Act
        result = categorize_path(temp_file.name)

        # Assert
        self.assertEqual(result[0], temp_file.name)
        self.assertIn(ICON_FILE, result[1])
        self.assertIn("B", result[1])

        os.unlink(temp_file.name)

    def test_categorize_path_nonexistent_returns_open_icon(self):
        # Arrange
        fake_path = "/nonexistent/path/file.txt"

        # Act
        result = categorize_path(fake_path)

        # Assert
        self.assertEqual(result[0], fake_path)
        self.assertEqual(result[1], ICON_OPEN)


if __name__ == "__main__":
    _ = unittest.main()
