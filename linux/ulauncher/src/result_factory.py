from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

def create_result_item(icon: str, name: str, description: str, path: str = None) -> ExtensionResultItem:
    if path:
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
