from pathlib import Path

ICON = "images/icon.png"
PLOCATE_LIMIT = 50
PLOCATE_TIMEOUT = 3
FREQUENCY_FILE = Path.home() / ".cache" / "ulauncher-systemsearch-frequency.json"
DB_CACHE_DIR = Path.home() / ".cache" / "ulauncher_systemsearch_dbs"
PRUNE_THRESHOLD = 0.1
MAX_ENTRIES = 1000

PREF_EXTRA_DIRS = "extra_dirs"
PREF_HALF_LIFE = "frequency_half_life"
PREF_INDEX_MOUNTED = "index_mounted_drives"

DEFAULT_HALF_LIFE = "7"
DEFAULT_INDEX_MOUNTED = "true"

MEDIA_DIR = "/media"
SYSTEM_DB_PATH = "/var/lib/plocate/plocate.db"
FALLBACK_DB_PATH = "/var/lib/mlocate/mlocate.db"

ICON_DIRECTORY = "📁 Directory"
ICON_FILE = "📄 File"
ICON_OPEN = "Open"
