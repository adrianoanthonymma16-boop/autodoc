"""
DocumentoService - carrega anexos (imagem, pdf, heic)
"""
import os
from PIL import Image
from validadores import validar_extensao
from anexo_pdf import pdf_para_imagem
from anexo_heic import heic_para_imagem

class DocumentoService:
    def __init__(self, state):
        self.state = state

    def anexar(self, caminho: str):
        valido, ext, msg = validar_extensao(caminho, 'anexo')
        if not valido:
            return False, msg
        try:
            if ext == '.pdf':
                imagem = pdf_para_imagem(caminho)
                tipo = 'pdf'
            elif ext == '.heic':
                imagem = heic_para_imagem(caminho)
                tipo = 'heic'
            else:
                imagem = Image.open(caminho).convert("RGB")
                tipo = 'imagem'
            # garante que não duplica
            for d in self.state.documentos_anexados:
                if d['caminho'] == caminho:
                    return False, "Documento já anexado"
            self.state.documentos_anexados.append({
                'caminho': caminho,
                'nome': os.path.basename(caminho),
                'tipo': tipo,
                'imagem_original': imagem
            })
            self.state.notify('documentos')
            return True, f"Anexado: {os.path.basename(caminho)}"
        except Exception as e:
            return False, str(e)

    def remover_por_path(self, caminho: str):
        for i, doc in enumerate(self.state.documentos_anexados):
            if doc['caminho'] == caminho:
                self.state.documentos_anexados.pop(i)
                # remove mapeamentos ligados
                remover = [ph for ph, dados in self.state.mapeamento.items() if dados['documento_path'] == caminho]
                for ph in remover:
                    del self.state.mapeamento[ph]
                self.state.lote_fontes = [e for e in self.state.lote_fontes if e['documento_path'] != caminho]
                if self.state.documento_atual_path == caminho:
                    self.state.documento_atual_path = None
                self.state.notify('documentos')
                self.state.notify('mapeamento')
                return True
        return False

    def selecionar(self, caminho: str):
        for doc in self.state.documentos_anexados:
            if doc['caminho'] == caminho:
                self.state.documento_atual_path = doc['caminho']
                self.state.documento_tipo = doc['tipo']
                self.state.notify('doc_selecionado')
                return doc
        return None
