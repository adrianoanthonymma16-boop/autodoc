"""
ModeloService - centraliza carregamento/validação de modelos
"""

from modelo_docx import docx_suportado, extrair_placeholders_docx
from modelo_odt import extrair_placeholders_odt
from validadores import validar_extensao


class ModeloService:
    def __init__(self, state):
        self.state = state

    def carregar_arquivo_unico(self, caminho: str) -> tuple[bool, str]:
        valido, ext, msg = validar_extensao(caminho, 'modelo')
        if not valido:
            return False, msg
        try:
            if ext == '.odt':
                phs = extrair_placeholders_odt(caminho)
                tipo = 'odt'
            elif ext == '.docx':
                if not docx_suportado():
                    return False, "Suporte a DOCX não disponível"
                phs = extrair_placeholders_docx(caminho)
                tipo = 'docx'
            else:
                return False, "Extensão não suportada"
            if not phs:
                return False, "Nenhum placeholder {{...}} encontrado."
            self.state.modelos = []
            self.state.placeholders_por_modelo = {}
            self.state.placeholders = sorted(list(phs))
            self.state.modelo_path = caminho
            self.state.modelo_tipo = tipo
            self.state.notify('modelo')
            return True, f"{len(phs)} placeholders"
        except Exception as e:
            return False, str(e)

    def adicionar_ao_lote(self, caminho: str) -> tuple[bool, str]:
        valido, ext, msg = validar_extensao(caminho, 'modelo')
        if not valido:
            return False, msg
        for m in self.state.modelos:
            if m['path'] == caminho:
                return False, "Modelo já anexado ao lote"
        try:
            if ext == '.odt':
                phs = list(extrair_placeholders_odt(caminho))
                tipo = 'odt'
            elif ext == '.docx':
                if not docx_suportado():
                    return False, "DOCX não suportado"
                phs = list(extrair_placeholders_docx(caminho))
                tipo = 'docx'
            else:
                return False, "Extensão não suportada"
            if not phs:
                return False, "Nenhum placeholder encontrado neste arquivo"
            self.state.modelos.append({'path': caminho, 'tipo': tipo, 'placeholders': phs})
            if not self.state.modelo_path:
                self.state.modelo_path = caminho
                self.state.modelo_tipo = tipo
            self._recalc_unificados()
            self.state.notify('modelo')
            self.state.notify('modelos')
            return True, f"{len(phs)} placeholders"
        except Exception as e:
            return False, str(e)

    def _recalc_unificados(self):
        all_phs = set()
        self.state.placeholders_por_modelo = {}
        for m in self.state.modelos:
            phs = set(m['placeholders'])
            all_phs.update(phs)
            self.state.placeholders_por_modelo[m['path']] = phs
        self.state.placeholders = sorted(list(all_phs))

    def remover_do_lote(self, idx: int):
        if 0 <= idx < len(self.state.modelos):
            self.state.modelos.pop(idx)
            if self.state.modelos:
                self.state.modelo_path = self.state.modelos[0]['path']
                self.state.modelo_tipo = self.state.modelos[0]['tipo']
            else:
                self.state.modelo_path = None
                self.state.modelo_tipo = None
            if self.state.modelos:
                self._recalc_unificados()
            else:
                self.state.placeholders = []
                self.state.placeholders_por_modelo = {}
            self.state.notify('modelo')
            self.state.notify('modelos')

    def usar_da_biblioteca(self, caminho: str, tipo: str, placeholders: list[str]):
        self.state.modelo_path = caminho
        self.state.modelo_tipo = tipo
        self.state.placeholders = placeholders
        self.state.notify('modelo')
