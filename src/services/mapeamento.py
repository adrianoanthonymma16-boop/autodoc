"""
MapeamentoService - lógica de mapeamento, undo/redo, import/export, backup atômico
Corrige bugs: undo invertido, desync lote_fontes, pan offset, etc.
"""
import json
import os
import copy
from typing import Dict, List

from config import BACKUP_FILE


class MapeamentoService:
    def __init__(self, state):
        self.state = state

    # --- core ---
    def adicionar(self, placeholder: str, doc_path: str, doc_tipo: str, x1: int, y1: int, x2: int, y2: int):
        # undo handling
        if placeholder in self.state.mapeamento:
            self.state.undo_stack.append({
                'action': 'update',
                'placeholder': placeholder,
                'old_data': copy.deepcopy(self.state.mapeamento[placeholder])
            })
        else:
            self.state.undo_stack.append({'action': 'add', 'placeholder': placeholder})
        self.state.redo_stack.clear()

        self.state.mapeamento[placeholder] = {
            'documento_path': doc_path,
            'documento_tipo': doc_tipo,
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2
        }
        self._sync_lote(placeholder, doc_path, doc_tipo, x1, y1, x2, y2)
        self.state.notify('mapeamento')

    def _sync_lote(self, placeholder, doc_path, doc_tipo, x1, y1, x2, y2):
        mapping = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
        for entry in self.state.lote_fontes:
            if entry['documento_path'] == doc_path:
                entry['mapeamento'][placeholder] = mapping
                return
        self.state.lote_fontes.append({
            'documento_path': doc_path,
            'documento_tipo': doc_tipo,
            'mapeamento': {placeholder: mapping}
        })

    def remover_placeholder(self, placeholder: str):
        if placeholder not in self.state.mapeamento:
            return
        old = copy.deepcopy(self.state.mapeamento[placeholder])
        doc_path = old['documento_path']
        self.state.undo_stack.append({
            'action': 'remove',
            'placeholder': placeholder,
            'old_data': old
        })
        self.state.redo_stack.clear()
        del self.state.mapeamento[placeholder]
        # sync lote
        for entry in list(self.state.lote_fontes):
            if placeholder in entry['mapeamento']:
                del entry['mapeamento'][placeholder]
                if not entry['mapeamento']:
                    self.state.lote_fontes.remove(entry)
        self.state.notify('mapeamento')

    def limpar(self):
        self.state.mapeamento.clear()
        self.state.lote_fontes.clear()
        self.state.undo_stack.clear()
        self.state.redo_stack.clear()
        self.state.notify('mapeamento')

    def limpar_lote(self):
        self.state.lote_fontes.clear()
        self.state.notify('mapeamento')

    # --- undo/redo corrigido ---
    def desfazer(self):
        if not self.state.undo_stack:
            return False, "Nada para desfazer."
        action = self.state.undo_stack.pop()
        ph = action['placeholder']
        if action['action'] == 'add':
            # desfaz adição -> remove
            old = copy.deepcopy(self.state.mapeamento.get(ph, {}))
            self.state.redo_stack.append({'action': 'add', 'placeholder': ph, 'old_data': old})
            if ph in self.state.mapeamento:
                doc_path = self.state.mapeamento[ph]['documento_path']
                del self.state.mapeamento[ph]
                # remove do lote também
                for entry in list(self.state.lote_fontes):
                    if ph in entry.get('mapeamento', {}):
                        del entry['mapeamento'][ph]
                        if not entry['mapeamento']:
                            self.state.lote_fontes.remove(entry)
        elif action['action'] == 'update':
            self.state.redo_stack.append({
                'action': 'update',
                'placeholder': ph,
                'old_data': copy.deepcopy(self.state.mapeamento.get(ph, {}))
            })
            self.state.mapeamento[ph] = action['old_data']
            # sync lote
            old = action['old_data']
            self._sync_lote(ph, old['documento_path'], old['documento_tipo'], old['x1'], old['y1'], old['x2'], old['y2'])
        elif action['action'] == 'remove':
            self.state.redo_stack.append({'action': 'remove', 'placeholder': ph})
            self.state.mapeamento[ph] = action['old_data']
            old = action['old_data']
            self._sync_lote(ph, old['documento_path'], old['documento_tipo'], old['x1'], old['y1'], old['x2'], old['y2'])
        self.state.notify('mapeamento')
        return True, f"Desfeito: {ph}"

    def refazer(self):
        if not self.state.redo_stack:
            return False, "Nada para refazer."
        action = self.state.redo_stack.pop()
        ph = action['placeholder']
        if action['action'] == 'add':
            # refaz adição: restaura old_data
            self.state.undo_stack.append({'action': 'add', 'placeholder': ph})
            if action.get('old_data'):
                old = action['old_data']
                if old:
                    self.state.mapeamento[ph] = old
                    self._sync_lote(ph, old['documento_path'], old['documento_tipo'], old['x1'], old['y1'], old['x2'], old['y2'])
        elif action['action'] == 'update':
            self.state.undo_stack.append({
                'action': 'update',
                'placeholder': ph,
                'old_data': copy.deepcopy(self.state.mapeamento.get(ph, {}))
            })
            self.state.mapeamento[ph] = action['old_data']
            old = action['old_data']
            self._sync_lote(ph, old['documento_path'], old['documento_tipo'], old['x1'], old['y1'], old['x2'], old['y2'])
        elif action['action'] == 'remove':
            self.state.undo_stack.append({
                'action': 'remove',
                'placeholder': ph,
                'old_data': copy.deepcopy(self.state.mapeamento.get(ph, {}))
            })
            if ph in self.state.mapeamento:
                del self.state.mapeamento[ph]
            for entry in list(self.state.lote_fontes):
                if ph in entry.get('mapeamento', {}):
                    del entry['mapeamento'][ph]
                    if not entry['mapeamento']:
                        self.state.lote_fontes.remove(entry)
        self.state.notify('mapeamento')
        return True, f"Refeito: {ph}"

    # --- export/import ---
    def exportar(self, caminho: str):
        if not self.state.mapeamento:
            raise ValueError("Nenhum mapeamento para exportar.")
        export = {
            'modelo_path': self.state.modelo_path,
            'modelo_tipo': self.state.modelo_tipo,
            'placeholders': self.state.placeholders,
            'mapeamento': self.state.mapeamento,
            'lote_fontes': self.state.lote_fontes,
            'modelos': self.state.modelos
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(export, f, indent=2, ensure_ascii=False)

    def importar(self, caminho: str, forcar: bool = False):
        with open(caminho, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data.get('modelo_path') != self.state.modelo_path and not forcar:
            # caller deve confirmar
            pass
        self.state.mapeamento = {}
        for ph, dados in data.get('mapeamento', {}).items():
            self.state.mapeamento[ph] = {
                'documento_path': dados['documento_path'],
                'documento_tipo': dados['documento_tipo'],
                'x1': dados['x1'], 'y1': dados['y1'], 'x2': dados['x2'], 'y2': dados['y2']
            }
        self.state.lote_fontes = data.get('lote_fontes', [])
        self.state.modelos = data.get('modelos', [])
        self.state.placeholders_por_modelo = {}
        for m in self.state.modelos:
            self.state.placeholders_por_modelo[m['path']] = set(m['placeholders'])
        self.state.undo_stack.clear()
        self.state.redo_stack.clear()
        self.state.notify('mapeamento')
        self.state.notify('modelos')

    # --- backup atômico ---
    def backup(self):
        if not (self.state.mapeamento and self.state.modelo_path):
            return
        backup = {
            'modelo_path': self.state.modelo_path,
            'modelo_tipo': self.state.modelo_tipo,
            'placeholders': self.state.placeholders,
            'mapeamento': self.state.mapeamento,
            'lote_fontes': self.state.lote_fontes,
            'modelos': self.state.modelos
        }
        os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
        tmp = BACKUP_FILE + ".tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(backup, f, indent=2, ensure_ascii=False)
            os.replace(tmp, BACKUP_FILE)
        except Exception:
            pass

    def restaurar_backup(self):
        if not os.path.exists(BACKUP_FILE):
            return None
        try:
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                backup = json.load(f)
            if not backup.get('mapeamento'):
                return None
            # verifica se modelo ainda existe
            mp = backup.get('modelo_path')
            if mp and not os.path.exists(mp):
                # tenta mas avisa
                pass
            return backup
        except Exception:
            return None

    def aplicar_backup(self, backup):
        self.state.modelo_path = backup.get('modelo_path')
        self.state.modelo_tipo = backup.get('modelo_tipo')
        self.state.placeholders = backup.get('placeholders', [])
        self.state.mapeamento = {}
        for ph, dados in backup.get('mapeamento', {}).items():
            self.state.mapeamento[ph] = {
                'documento_path': dados['documento_path'],
                'documento_tipo': dados['documento_tipo'],
                'x1': dados['x1'], 'y1': dados['y1'], 'x2': dados['x2'], 'y2': dados['y2']
            }
        self.state.lote_fontes = backup.get('lote_fontes', [])
        self.state.modelos = backup.get('modelos', [])
        self.state.placeholders_por_modelo = {}
        for m in self.state.modelos:
            self.state.placeholders_por_modelo[m['path']] = set(m['placeholders'])
        self.state.notify('backup')
        self.state.notify('mapeamento')
        self.state.notify('modelos')
