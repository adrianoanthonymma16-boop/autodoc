"""Tests for EventBus"""
from core.bus import EventBus


class TestEventBus:
    def test_on_and_emit(self, event_bus):
        received = []
        event_bus.on("click", lambda: received.append(1))
        event_bus.emit("click")
        assert received == [1]

    def test_emit_no_subscribers(self, event_bus):
        # Should not raise
        event_bus.emit("nonexistent")

    def test_multiple_subscribers(self, event_bus):
        results = []
        event_bus.on("x", lambda: results.append("a"))
        event_bus.on("x", lambda: results.append("b"))
        event_bus.emit("x")
        assert results == ["a", "b"]

    def test_different_events_independent(self, event_bus):
        a, b = [], []
        event_bus.on("ev1", lambda: a.append(1))
        event_bus.on("ev2", lambda: b.append(1))
        event_bus.emit("ev1")
        assert a == [1]
        assert b == []

    def test_emit_with_kwargs(self, event_bus):
        results = []
        event_bus.on("data", lambda x=0, y=0: results.append((x, y)))
        event_bus.emit("data", x=10, y=20)
        assert results == [(10, 20)]

    def test_swallows_exceptions(self, event_bus):
        def bad_cb():
            raise ValueError("boom")

        good = []
        event_bus.on("ev", bad_cb)
        event_bus.on("ev", lambda: good.append("ok"))
        event_bus.emit("ev")
        assert good == ["ok"]
