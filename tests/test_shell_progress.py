"""Barra de progresso da sidebar: razão sem divisão por zero."""
from types import SimpleNamespace

from ui.shell import Shell


class _Bar:
    def __init__(self):
        self.value = None
        self.options = {}

    def set(self, value):
        self.value = value

    def configure(self, **kwargs):
        self.options.update(kwargs)


class _Label:
    def __init__(self):
        self.text = None

    def configure(self, **kwargs):
        self.text = kwargs.get("text")


def _fake(done: int, total: int):
    return SimpleNamespace(
        state=SimpleNamespace(
            placeholders=list(range(total)),
            mapeamento={str(i): {} for i in range(done)},
        ),
        step_bar=_Bar(),
        step_label=_Label(),
    )


def test_progresso_sem_placeholders_fica_zerado():
    fake = _fake(0, 0)
    Shell._on_state_progress(fake, "init")
    assert fake.step_bar.value == 0
    assert fake.step_label.text == "Progresso"


def test_progresso_parcial_e_completo():
    fake = _fake(1, 2)
    Shell._on_state_progress(fake, "mapeamento")
    assert fake.step_bar.value == 0.5
    assert fake.step_label.text == "1/2 mapeados"

    fake = _fake(2, 2)
    Shell._on_state_progress(fake, "mapeamento")
    assert fake.step_bar.value == 1
    assert fake.step_label.text == "2/2 mapeados"
