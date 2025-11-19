from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import PreferencesUpdateEvent

class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event: PreferencesUpdateEvent, extension):
        prefs = extension.preferences.copy()
        prefs[event.id] = event.new_value
        extension.update_dbs_from_prefs(prefs)
