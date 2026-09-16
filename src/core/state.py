"""
AppState - estado centralizado observável
Desacopla lógica de UI: views observam mudanças via callbacks
"""
import contextlib
import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    # Modelos
    modelo_path: str | None = None
    modelo_tipo: str | None = None
    placeholders: list[str] = field(default_factory=list)
    modelos: list[dict] = field(default_factory=list)  # lote
    placeholders_por_modelo: dict[str, set] = field(default_factory=dict)

    # Documentos anexados
    documentos_anexados: list[dict] = field(default_factory=list)
    documento_atual_path: str | None = None
    documento_tipo: str | None = None
    placeholder_atual: str | None = None

    # Mapeamento
    mapeamento: dict[str, dict] = field(default_factory=dict)
    lote_fontes: list[dict] = field(default_factory=list)

    # Dados extraídos
    dados_extraidos: dict[str, str] = field(default_factory=dict)

    # UI state
    zoom_level: float = 1.0
    tema: str = "light"

    # undo/redo stacks - stored as list of actions
    undo_stack: list[dict] = field(default_factory=list)
    redo_stack: list[dict] = field(default_factory=list)

    # observers
    _listeners: list[Callable] = field(default_factory=list, repr=False)

    def subscribe(self, cb: Callable[[str], None]):
        self._listeners.append(cb)

    def notify(self, event: str):
        for cb in self._listeners:
            with contextlib.suppress(Exception):
                cb(event)

    def snapshot(self) -> dict[str, Any]:
        return {
            'modelo_path': self.modelo_path,
            'modelo_tipo': self.modelo_tipo,
            'placeholders': list(self.placeholders),
            'mapeamento': copy.deepcopy(self.mapeamento),
            'lote_fontes': copy.deepcopy(self.lote_fontes),
            'modelos': copy.deepcopy(self.modelos),
        }
