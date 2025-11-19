import subprocess
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

from src.constants import ICON, PREF_HALF_LIFE, DEFAULT_HALF_LIFE
from src.frequency import load_frequency, save_frequency, prune_frequency
from src.search import search_plocate, categorize_and_sort
from src.result_factory import create_result_item

class KeywordQueryEventListener(EventListener):
    def on_event(self, event: KeywordQueryEvent, extension) -> RenderResultListAction:
        query = event.get_argument() or ""

        try:
            half_life_days = float(extension.preferences.get(PREF_HALF_LIFE, DEFAULT_HALF_LIFE))
        except:
            half_life_days = float(DEFAULT_HALF_LIFE)

        if not query:
            return RenderResultListAction([
                create_result_item(ICON, "Type to search files...", "Search your system using plocate")
            ])

        try:
            db_paths = extension.db_manager.get_db_paths()
            paths = search_plocate(query, db_paths=db_paths)
            frequency = load_frequency()

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
