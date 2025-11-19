from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import ItemEnterEvent
from src.frequency import increment_frequency

class ItemEnterEventListener(EventListener):
    def on_event(self, event: ItemEnterEvent, extension):
        data = event.get_data()
        if data:
            increment_frequency(data)
