"""Tests for AppState"""
import copy
from core.state import AppState


class TestAppState:
    def test_default_state(self):
        s = AppState()
        assert s.modelo_path is None
        assert s.modelo_tipo is None
        assert s.placeholders == []
        assert s.mapeamento == {}
        assert s.zoom_level == 1.0
        assert s.tema == "light"

    def test_subscribe_and_notify(self, app_state):
        events = []
        app_state.subscribe(lambda e: events.append(e))
        app_state.notify("test_event")
        assert events == ["test_event"]

    def test_notify_multiple_listeners(self, app_state):
        results = []
        app_state.subscribe(lambda e: results.append("a"))
        app_state.subscribe(lambda e: results.append("b"))
        app_state.notify("x")
        assert results == ["a", "b"]

    def test_notify_swallows_exceptions(self, app_state):
        def bad_cb(e):
            raise ValueError("boom")

        good = []
        app_state.subscribe(bad_cb)
        app_state.subscribe(lambda e: good.append("ok"))
        app_state.notify("test")
        assert good == ["ok"]

    def test_snapshot_copies_data(self, app_state):
        app_state.placeholders = ["A", "B"]
        app_state.mapeamento = {"A": {"doc": "x"}}
        snap = app_state.snapshot()
        # Mutating original shouldn't affect snapshot
        app_state.placeholders.append("C")
        app_state.mapeamento["B"] = {"doc": "y"}
        assert snap["placeholders"] == ["A", "B"]
        assert "B" not in snap["mapeamento"]

    def test_snapshot_is_dict(self, app_state):
        snap = app_state.snapshot()
        assert isinstance(snap, dict)
        assert "modelo_path" in snap
        assert "mapeamento" in snap
