"""
EventBus simples para comunicação entre módulos sem acoplamento
"""
import contextlib
from collections.abc import Callable


class EventBus:
    def __init__(self):
        self._subs: dict[str, list[Callable]] = {}

    def on(self, event: str, cb: Callable):
        self._subs.setdefault(event, []).append(cb)

    def emit(self, event: str, **kwargs):
        for cb in self._subs.get(event, []):
            with contextlib.suppress(Exception):
                cb(**kwargs)

bus = EventBus()
