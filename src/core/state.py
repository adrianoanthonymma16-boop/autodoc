"""
AppState - estado centralizado observável
Desacopla lógica de UI: views observam mudanças via callbacks
"""
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional, Any
import copy


@dataclass
class AppState:
    # Modelos
    modelo_path: Optional[str] = None
    modelo_tipo: Optional[str] = None
    placeholders: List[str] = field(default_factory=list)
    modelos: List[Dict] = field(default_factory=list)  # lote
    placeholders_por_modelo: Dict[str, set] = field(default_factory=dict)

    # Documentos anexados
    documentos_anexados: List[Dict] = field(default_factory=list)
    documento_atual_path: Optional[str] = None
    documento_tipo: Optional[str] = None
    placeholder_atual: Optional[str] = None

    # Mapeamento
    mapeamento: Dict[str, Dict] = field(default_factory=dict)
    lote_fontes: List[Dict] = field(default_factory=list)

    # Dados extraídos
    dados_extraidos: Dict[str, str] = field(default_factory=dict)

    # UI state
    zoom_level: float = 1.0
    tema: str = "light"

    # undo/redo stacks - stored as list of actions
    undo_stack: List[Dict] = field(default_factory=list)
    redo_stack: List[Dict] = field(default_factory=list)

    # observers
    _listeners: List[Callable] = field(default_factory=list, repr=False)

    def subscribe(self, cb: Callable[[str], None]):
        self._listeners.append(cb)

    def notify(self, event: str):
        for cb in self._listeners:
            try:
                cb(event)
            except Exception:
                pass

    def snapshot(self) -> Dict[str, Any]:
        return {
            'modelo_path': self.modelo_path,
            'modelo_tipo': self.modelo_tipo,
            'placeholders': list(self.placeholders),
            'mapeamento': copy.deepcopy(self.mapeamento),
            'lote_fontes': copy.deepcopy(self.lote_fontes),
            'modelos': copy.deepcopy(self.modelos),
        }
