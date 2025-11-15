"""System Search - Ulauncher extension for plocate file search."""
import json
import math
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem


ICON = "images/icon.png"
PLOCATE_LIMIT = 50
PLOCATE_TIMEOUT = 3
FREQUENCY_FILE = Path.home() / ".cache" / "ulauncher-systemsearch-frequency.json"
PRUNE_THRESHOLD = 0.1  # Prune entries with effective count < 0.1
MAX_ENTRIES = 1000  # Max entries before aggressive pruning


def load_frequency() -> Dict[str, Dict]:
    """Load path access frequency from cache."""
    try:
        if FREQUENCY_FILE.exists():
            return json.loads(FREQUENCY_FILE.read_text())
    except:
        pass
    return {}


def save_frequency(frequency: Dict[str, Dict]):
    """Save path access frequency to cache."""
    try:
        FREQUENCY_FILE.parent.mkdir(parents=True, exist_ok=True)
        FREQUENCY_FILE.write_text(json.dumps(frequency, indent=2))
    except:
        pass


def calculate_decay(days_since_access: float, half_life_days: float) -> float:
    """Calculate exponential decay factor based on time elapsed."""
    return math.exp(-days_since_access * math.log(2) / half_life_days)


def get_effective_count(entry: Dict, half_life_days: float) -> float:
    """Calculate effective count with time-based decay."""
    count = entry.get("count", 0)
    last_accessed = entry.get("last_accessed")

    if not last_accessed:
        return 0

    try:
        last_time = datetime.fromisoformat(last_accessed)
        days_elapsed = (datetime.now() - last_time).total_seconds() / 86400
        decay_factor = calculate_decay(days_elapsed, half_life_days)
        return count * decay_factor
    except:
        return 0


def prune_frequency(frequency: Dict[str, Dict], half_life_days: float):
    """Remove low-value entries to keep file size manageable."""
    # Calculate effective counts for all entries
    entries_with_scores = [
        (path, get_effective_count(entry, half_life_days))
        for path, entry in frequency.items()
    ]

    # Remove entries below threshold
    to_remove = [path for path, score in entries_with_scores if score < PRUNE_THRESHOLD]
    for path in to_remove:
        del frequency[path]

    # If still too many entries, keep only the top MAX_ENTRIES
    if len(frequency) > MAX_ENTRIES:
        entries_with_scores = [
            (path, get_effective_count(entry, half_life_days))
            for path, entry in frequency.items()
        ]
        sorted_entries = sorted(entries_with_scores, key=lambda x: x[1], reverse=True)
        keep_paths = set(path for path, _ in sorted_entries[:MAX_ENTRIES])
        frequency_copy = frequency.copy()
        for path in frequency_copy:
            if path not in keep_paths:
                del frequency[path]


def increment_frequency(path: str):
    """Increment access count for a path."""
    frequency = load_frequency()

    # Update or create entry
    if path in frequency:
        frequency[path]["count"] = frequency[path].get("count", 0) + 1
        frequency[path]["last_accessed"] = datetime.now().isoformat()
    else:
        frequency[path] = {
            "count": 1,
            "last_accessed": datetime.now().isoformat()
        }

    save_frequency(frequency)


def score_path(path: str, frequency: Dict[str, Dict], half_life_days: float) -> int:
    """Calculate relevance score for a path (lower = more relevant)."""
    parts = path.split('/')
    hidden_penalty = sum(1000 for part in parts if part.startswith('.'))
    depth_penalty = len(parts) * 10
    length_penalty = len(path)

    # Boost frequently accessed paths with time-based decay
    effective_count = 0
    if path in frequency:
        effective_count = get_effective_count(frequency[path], half_life_days)

    frequency_bonus = effective_count * -50

    return hidden_penalty + depth_penalty + length_penalty + frequency_bonus


def format_file_size(size: int) -> str:
    """Format file size in human-readable format."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"


def categorize_path(path: str) -> Tuple[str, str]:
    """Categorize a path and return (path, description) tuple."""
    if os.path.isdir(path):
        return (path, "📁 Directory")
    if os.path.isfile(path):
        try:
            size = os.path.getsize(path)
            return (path, f"📄 File ({format_file_size(size)})")
        except:
            return (path, "📄 File")
    return (path, "Open")


def categorize_and_sort(paths: List[str], frequency: Dict[str, Dict], half_life_days: float) -> List[Tuple[str, str]]:
    """Categorize paths and sort by type and relevance."""
    categorized = [categorize_path(p) for p in paths]
    dirs = [item for item in categorized if "📁" in item[1]]
    files = [item for item in categorized if "📄" in item[1]]
    others = [item for item in categorized if item not in dirs and item not in files]

    return (
        sorted(dirs, key=lambda x: score_path(x[0], frequency, half_life_days)) +
        sorted(files, key=lambda x: score_path(x[0], frequency, half_life_days)) +
        sorted(others, key=lambda x: score_path(x[0], frequency, half_life_days))
    )


def search_plocate(query: str) -> List[str]:
    """Search using plocate, returns list of matching paths."""
    words = query.split()
    if len(words) > 1:
        pattern = '.*' + '.*'.join(words) + '.*'
        cmd = ["plocate", "--regexp", "--ignore-case", "--limit", str(PLOCATE_LIMIT), pattern]
    else:
        cmd = ["plocate", "--ignore-case", "--limit", str(PLOCATE_LIMIT), query]

    try:
        result = subprocess.check_output(cmd, text=True, timeout=PLOCATE_TIMEOUT, stderr=subprocess.DEVNULL)
        return result.splitlines()
    except subprocess.CalledProcessError:
        return []


def create_result_item(icon: str, name: str, description: str, path: str = None) -> ExtensionResultItem:
    """Create an ExtensionResultItem."""
    if path:
        # Create a bash script that tracks frequency and opens the path
        # Use shell variable to avoid f-string quoting issues
        script = f"""#!/bin/bash
export PATH_VAR={repr(path)}
python3 -c "
import json
from pathlib import Path
from datetime import datetime
import os

frequency_file = Path.home() / '.cache' / 'ulauncher-systemsearch-frequency.json'
path = os.environ['PATH_VAR']
try:
    frequency = json.loads(frequency_file.read_text()) if frequency_file.exists() else {{}}
    if path in frequency:
        frequency[path]['count'] = frequency[path].get('count', 0) + 1
        frequency[path]['last_accessed'] = datetime.now().isoformat()
    else:
        frequency[path] = {{'count': 1, 'last_accessed': datetime.now().isoformat()}}
    frequency_file.parent.mkdir(parents=True, exist_ok=True)
    frequency_file.write_text(json.dumps(frequency, indent=2))
except:
    pass
"
xdg-open "$PATH_VAR"
"""
        return ExtensionResultItem(
            icon=icon,
            name=name,
            description=description,
            on_enter=RunScriptAction(script, [])
        )
    else:
        return ExtensionResultItem(
            icon=icon,
            name=name,
            description=description
        )


class ItemEnterEventListener(EventListener):
    """Track when items are opened to update frequency."""

    def on_event(self, event: ItemEnterEvent, extension):
        """Handle item enter event."""
        data = event.get_data()
        if data:
            increment_frequency(data)


class KeywordQueryEventListener(EventListener):
    """Handles keyword query events from Ulauncher."""

    def on_event(self, event: KeywordQueryEvent, extension) -> RenderResultListAction:
        """Handle keyword query event."""
        query = event.get_argument() or ""

        # Get half-life preference (default to 7 days)
        try:
            half_life_days = float(extension.preferences.get("frequency_half_life", "7"))
        except:
            half_life_days = 7.0

        if not query:
            return RenderResultListAction([
                create_result_item(ICON, "Type to search files...", "Search your system using plocate")
            ])

        try:
            paths = search_plocate(query)
            frequency = load_frequency()

            # Prune old/low-value entries periodically
            prune_frequency(frequency, half_life_days)
            save_frequency(frequency)

            sorted_results = categorize_and_sort(paths, frequency, half_life_days)

            if not sorted_results:
                return RenderResultListAction([
                    create_result_item(ICON, "No results found", f"No files matching '{query}'")
                ])

            items = [create_result_item(ICON, path, desc, path) for path, desc in sorted_results]
            return RenderResultListAction(items)

        except subprocess.TimeoutExpired:
            return RenderResultListAction([
                create_result_item(ICON, "Search timeout", "Query took too long, try being more specific")
            ])
        except FileNotFoundError:
            return RenderResultListAction([
                create_result_item(ICON, "plocate not installed", "Install with: sudo apt install plocate")
            ])
        except Exception as e:
            return RenderResultListAction([
                create_result_item(ICON, "Error running plocate", str(e))
            ])


class SystemSearchExtension(Extension):
    """Ulauncher extension for system-wide file search."""

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


if __name__ == "__main__":
    SystemSearchExtension().run()
