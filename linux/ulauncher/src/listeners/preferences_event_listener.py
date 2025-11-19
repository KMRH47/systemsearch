from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import PreferencesEvent

class PreferencesEventListener(EventListener):
    def on_event(self, event: PreferencesEvent, extension):
        extension.update_dbs_from_prefs(event.preferences)
