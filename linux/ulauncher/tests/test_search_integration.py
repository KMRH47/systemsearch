from __future__ import annotations

import os
import shutil
import sys
import unittest
from pathlib import Path as PathlibPath
from typing import override
from unittest.mock import patch

sys.path.append(os.path.abspath("linux/ulauncher"))

from src import db_manager, search  # pyright: ignore[reportImplicitRelativeImport]


class TestSearchIntegration(unittest.TestCase):
    test_dir: str = ""
    extra_dir: str = ""
    test_file: str = ""
    cache_dir: str = ""

    @override
    def setUp(self) -> None:
        self.test_dir = os.path.abspath("tests/tmp_test_dir")
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

        self.extra_dir = os.path.join(self.test_dir, "extra")
        os.makedirs(self.extra_dir)
        self.test_file = os.path.join(self.extra_dir, "test_unique_file.txt")
        with open(self.test_file, "w") as f:
            _ = f.write("content")

        self.cache_dir = os.path.join(self.test_dir, "cache")
        os.makedirs(self.cache_dir)

    @override
    def tearDown(self) -> None:
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_db_manager_extra_directories_creates_database_and_finds_files(self):
        # Arrange
        manager = db_manager.DbManager(self.cache_dir)
        manager.update_dbs([self.extra_dir], auto_mounts=False)
        db_paths = manager.get_db_paths()

        # Act
        results = search.search_plocate("test_unique_file", db_paths=db_paths)

        # Assert
        self.assertTrue(len(db_paths) > 0, "Should have created at least one DB")
        self.assertIn(self.test_file, results)

    def test_db_manager_auto_mount_detection_indexes_media_directories(self):
        # Arrange
        media_root = os.path.join(self.test_dir, "media")
        drive_dir = os.path.join(media_root, "test_drive")
        os.makedirs(drive_dir)

        drive_file = os.path.join(drive_dir, "drive_file.txt")
        with open(drive_file, "w") as f:
            _ = f.write("content")

        def side_effect(
            path: str | PathlibPath,
            *args: str | PathlibPath,
            **_: object,
        ) -> PathlibPath:
            if str(path) == "/media":
                return PathlibPath(media_root)
            return PathlibPath(path, *args)

        # Act
        with patch("src.db_manager.Path", side_effect=side_effect):
            manager = db_manager.DbManager(self.cache_dir)
            manager.update_dbs([], auto_mounts=True)
            db_paths = manager.get_db_paths()
            mounts = manager.get_mounted_drives()
            results = search.search_plocate("drive_file", db_paths=db_paths)

        # Assert
        self.assertIn(drive_dir, mounts)
        self.assertIn(drive_file, results)


if __name__ == "__main__":
    _ = unittest.main()
