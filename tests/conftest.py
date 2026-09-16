"""
Shared fixtures for AutoDoc tests
"""
import sys
import os
import pytest

# Ensure src/ is importable (same as run_ctk.py does)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def app_state():
    """Fresh AppState instance for each test"""
    from core.state import AppState
    return AppState()


@pytest.fixture
def event_bus():
    """Fresh EventBus instance for each test"""
    from core.bus import EventBus
    return EventBus()
