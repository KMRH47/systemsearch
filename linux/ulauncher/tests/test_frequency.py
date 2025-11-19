from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.append(os.path.abspath("linux/ulauncher"))
from src.frequency import calculate_decay, get_effective_count, prune_frequency, increment_frequency  # pyright: ignore[reportImplicitRelativeImport]
from src.models import FrequencyEntry, FrequencyData  # pyright: ignore[reportImplicitRelativeImport]

class TestFrequency(unittest.TestCase):
    def test_calculate_decay_zero_days_elapsed_returns_one(self):
        # Arrange
        days_elapsed = 0
        half_life_days = 7.0
        
        # Act
        result = calculate_decay(days_elapsed, half_life_days)
        
        # Assert
        self.assertAlmostEqual(result, 1.0, places=5)

    def test_calculate_decay_one_half_life_elapsed_returns_half(self):
        # Arrange
        days_elapsed = 7
        half_life_days = 7.0
        
        # Act
        result = calculate_decay(days_elapsed, half_life_days)
        
        # Assert
        self.assertAlmostEqual(result, 0.5, places=5)

    def test_calculate_decay_two_half_lives_elapsed_returns_quarter(self):
        # Arrange
        days_elapsed = 14
        half_life_days = 7.0
        
        # Act
        result = calculate_decay(days_elapsed, half_life_days)
        
        # Assert
        self.assertAlmostEqual(result, 0.25, places=5)

    def test_get_effective_count_recent_access_returns_full_count(self):
        # Arrange
        now = datetime.now()
        entry = FrequencyEntry(count=10, last_accessed=now.isoformat())
        half_life_days = 7.0
        
        # Act
        result = get_effective_count(entry, half_life_days)
        
        # Assert
        self.assertAlmostEqual(result, 10.0, places=1)

    def test_get_effective_count_old_access_returns_decayed_count(self):
        # Arrange
        old_time = datetime.now() - timedelta(days=14)
        entry = FrequencyEntry(count=10, last_accessed=old_time.isoformat())
        half_life_days = 7.0
        
        # Act
        result = get_effective_count(entry, half_life_days)
        
        # Assert
        self.assertAlmostEqual(result, 2.5, places=1)

    def test_get_effective_count_no_last_accessed_returns_zero(self):
        # Arrange
        entry = FrequencyEntry(count=10, last_accessed=None)
        half_life_days = 7.0
        
        # Act
        result = get_effective_count(entry, half_life_days)
        
        # Assert
        self.assertEqual(result, 0)

    def test_prune_frequency_low_scores_removes_entries(self):
        # Arrange
        old_time = datetime.now() - timedelta(days=100)
        frequency = FrequencyData(entries={
            "/path/high": FrequencyEntry(count=100, last_accessed=datetime.now().isoformat()),
            "/path/low": FrequencyEntry(count=1, last_accessed=old_time.isoformat())
        })
        half_life_days = 7.0
        
        # Act
        prune_frequency(frequency, half_life_days)
        
        # Assert
        self.assertIn("/path/high", frequency.entries)
        self.assertNotIn("/path/low", frequency.entries)

    def test_increment_frequency_new_path_creates_entry_with_count_one(self):
        # Arrange
        test_path = "/test/new/path.txt"
        temp_file = Path("/tmp/test_freq_new.json")
        if temp_file.exists():
            temp_file.unlink()
        mock_now = datetime(2025, 1, 1, 12, 0, 0)
        
        # Act
        with patch("src.frequency.FREQUENCY_FILE", temp_file):
            with patch("src.frequency.datetime") as mock_dt:
                mock_dt.now.return_value = mock_now
                increment_frequency(test_path)

            from src.frequency import load_frequency  # pyright: ignore[reportImplicitRelativeImport]
            result = load_frequency()
        
        # Assert
        self.assertIn(test_path, result.entries)
        self.assertEqual(result.entries[test_path].count, 1)
        self.assertEqual(result.entries[test_path].last_accessed, mock_now.isoformat())
        
        if temp_file.exists():
            temp_file.unlink()

    def test_increment_frequency_existing_path_increments_count_and_updates_timestamp(self):
        # Arrange
        test_path = "/test/existing/path.txt"
        temp_file = Path("/tmp/test_freq_existing.json")
        if temp_file.exists():
            temp_file.unlink()
        mock_now1 = datetime(2025, 1, 1, 12, 0, 0)
        mock_now2 = datetime(2025, 1, 2, 12, 0, 0)
        
        # Act
        with patch("src.frequency.FREQUENCY_FILE", temp_file):
            with patch("src.frequency.datetime") as mock_dt:
                mock_dt.now.return_value = mock_now1
                increment_frequency(test_path)

                mock_dt.now.return_value = mock_now2
                increment_frequency(test_path)

            from src.frequency import load_frequency  # pyright: ignore[reportImplicitRelativeImport]
            result = load_frequency()
        
        # Assert
        self.assertEqual(result.entries[test_path].count, 2)
        self.assertEqual(result.entries[test_path].last_accessed, mock_now2.isoformat())
        
        if temp_file.exists():
            temp_file.unlink()

if __name__ == '__main__':
    _ = unittest.main()
