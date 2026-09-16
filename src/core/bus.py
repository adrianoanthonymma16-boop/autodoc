"""
EventBus simples para comunicação entre módulos sem acoplamento
"""
from typing import Callable, Dict, List

class EventBus:
    def __init__(self):
        self._subs: Dict[str, List[Callable]] = {}

    def on(self, event: str, cb: Callable):
        self._subs.setdefault(event, []).append(cb)

    def emit(self, event: str, **kwargs):
        for cb in self._subs.get(event, []):
            try:
                cb(**kwargs)
            except Exception:
                pass

bus = EventBus()
