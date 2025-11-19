from __future__ import annotations

import os
import subprocess

from .constants import (
    PLOCATE_LIMIT,
    PLOCATE_TIMEOUT,
    ICON_DIRECTORY,
    ICON_FILE,
    ICON_OPEN,
)
from .frequency import get_effective_count
from .models import FrequencyData


def score_path(path: str, frequency: FrequencyData, half_life_days: float) -> float:
    parts = path.split("/")
    hidden_penalty = sum(1000 for part in parts if part.startswith("."))
    depth_penalty = len(parts) * 10
    length_penalty = len(path)
    effective_count = 0.0
    entry = frequency.entries.get(path)
    if entry:
        effective_count = get_effective_count(entry, half_life_days)
    frequency_bonus = effective_count * -50
    return float(hidden_penalty + depth_penalty + length_penalty + frequency_bonus)


def format_file_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def categorize_path(path: str) -> tuple[str, str]:
    if os.path.isdir(path):
        return (path, ICON_DIRECTORY)
    if not os.path.isfile(path):
        return (path, ICON_OPEN)
    try:
        size = os.path.getsize(path)
        return (path, f"{ICON_FILE} ({format_file_size(size)})")
    except Exception:
        return (path, ICON_FILE)


def categorize_and_sort(
    paths: list[str], frequency: FrequencyData, half_life_days: float
) -> list[tuple[str, str]]:
    categorized = [categorize_path(p) for p in paths]
    dirs = [item for item in categorized if ICON_DIRECTORY in item[1]]
    files = [item for item in categorized if ICON_FILE in item[1]]
    others = [item for item in categorized if item not in dirs and item not in files]

    return (
        sorted(dirs, key=lambda x: score_path(x[0], frequency, half_life_days))
        + sorted(files, key=lambda x: score_path(x[0], frequency, half_life_days))
        + sorted(others, key=lambda x: score_path(x[0], frequency, half_life_days))
    )


def search_plocate(query: str, db_paths: list[str] | None = None) -> list[str]:
    import re
    words = query.split()
    if len(words) > 1:
        escaped_words = [re.escape(word) for word in words]
        pattern = ".*" + ".*".join(escaped_words) + ".*"
        args = ["--regexp", pattern]
    else:
        args = [query]
    base_cmd = ["plocate", "--ignore-case", "--limit", str(PLOCATE_LIMIT)]
    results: set[str] = set()
    try:
        sys_output = subprocess.check_output(
            base_cmd + args,
            text=True,
            timeout=PLOCATE_TIMEOUT,
            stderr=subprocess.DEVNULL,
        )
        results.update(sys_output.splitlines())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    if not db_paths:
        return list(results)
    custom_cmd = base_cmd.copy()
    for db in db_paths:
        custom_cmd.extend(["-d", db])
    try:
        custom_output = subprocess.check_output(
            custom_cmd + args,
            text=True,
            timeout=PLOCATE_TIMEOUT,
            stderr=subprocess.DEVNULL,
        )
        results.update(custom_output.splitlines())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    return list(results)
