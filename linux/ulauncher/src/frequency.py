import json
import math
from datetime import datetime
from typing import Dict
from .constants import FREQUENCY_FILE, PRUNE_THRESHOLD, MAX_ENTRIES
from .models import FrequencyData, FrequencyEntry

def load_frequency() -> FrequencyData:
    try:
        if FREQUENCY_FILE.exists():
            data = json.loads(FREQUENCY_FILE.read_text())
            if data and isinstance(data, dict) and "entries" not in data:
                first_val = next(iter(data.values()), None)
                if first_val and isinstance(first_val, dict) and "count" in first_val:
                    return FrequencyData(entries={k: FrequencyEntry(**v) for k, v in data.items()})
            
            return FrequencyData(**data)
    except:
        pass
    return FrequencyData()

def save_frequency(frequency: FrequencyData):
    try:
        FREQUENCY_FILE.parent.mkdir(parents=True, exist_ok=True)
        FREQUENCY_FILE.write_text(frequency.model_dump_json(indent=2))
    except:
        pass

def calculate_decay(days_since_access: float, half_life_days: float) -> float:
    return math.exp(-days_since_access * math.log(2) / half_life_days)

def get_effective_count(entry: FrequencyEntry, half_life_days: float) -> float:
    if not entry.last_accessed:
        return 0

    try:
        last_time = datetime.fromisoformat(entry.last_accessed)
        days_elapsed = (datetime.now() - last_time).total_seconds() / 86400
        decay_factor = calculate_decay(days_elapsed, half_life_days)
        return entry.count * decay_factor
    except:
        return 0

def prune_frequency(frequency: FrequencyData, half_life_days: float):
    entries_with_scores = [
        (path, get_effective_count(entry, half_life_days))
        for path, entry in frequency.entries.items()
    ]

    to_remove = [path for path, score in entries_with_scores if score < PRUNE_THRESHOLD]
    for path in to_remove:
        del frequency.entries[path]

    if len(frequency.entries) > MAX_ENTRIES:
        entries_with_scores = [
            (path, get_effective_count(entry, half_life_days))
            for path, entry in frequency.entries.items()
        ]
        sorted_entries = sorted(entries_with_scores, key=lambda x: x[1], reverse=True)
        keep_paths = set(path for path, _ in sorted_entries[:MAX_ENTRIES])
        
        frequency.entries = {
            path: entry 
            for path, entry in frequency.entries.items() 
            if path in keep_paths
        }

def increment_frequency(path: str):
    frequency = load_frequency()

    if path in frequency.entries:
        entry = frequency.entries[path]
        entry.count += 1
        entry.last_accessed = datetime.now().isoformat()
    else:
        frequency.entries[path] = FrequencyEntry(
            count=1,
            last_accessed=datetime.now().isoformat()
        )

    save_frequency(frequency)
