import threading

from ulauncher.api.client.Extension import Extension  # type: ignore[import-untyped]
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesEvent, PreferencesUpdateEvent  # type: ignore[import-untyped]

from .src.db_manager import DbManager
from .src.constants import PREF_EXTRA_DIRS, PREF_INDEX_MOUNTED, DEFAULT_INDEX_MOUNTED, DB_CACHE_DIR
from .src.listeners.keyword_query_event_listener import KeywordQueryEventListener
from .src.listeners.item_enter_event_listener import ItemEnterEventListener
from .src.listeners.preferences_event_listener import PreferencesEventListener
from .src.listeners.preferences_update_event_listener import PreferencesUpdateEventListener

class SystemSearchExtension(Extension):
    db_manager: DbManager

    def __init__(self) -> None:
        super().__init__()
        self.db_manager = DbManager(str(DB_CACHE_DIR))
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())
        self.update_dbs_from_prefs(self.preferences)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]

    def update_dbs_from_prefs(self, preferences: dict[str, str]) -> None:
        dirs_str = preferences.get(PREF_EXTRA_DIRS, "")
        auto_mounts_str = preferences.get(PREF_INDEX_MOUNTED, DEFAULT_INDEX_MOUNTED)
        auto_mounts = auto_mounts_str.lower() == "true"

        paths: list[str] = [p.strip() for p in dirs_str.split(",") if p.strip()]
        threading.Thread(target=self.db_manager.update_dbs, args=(paths, auto_mounts)).start()

if __name__ == "__main__":
    SystemSearchExtension().run()
