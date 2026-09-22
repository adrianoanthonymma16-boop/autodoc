"""
ExtracaoService - OCR em thread para não congelar UI
"""
import threading

from PIL import Image

from anexo_heic import heic_para_imagem
from anexo_pdf import pdf_para_imagem
from ocr import extrair_texto_do_recorte


class ExtracaoService:
    def __init__(self, state):
        self.state = state

    def extrair_todos(self, on_progress=None, on_done=None, on_error=None, marshal=None):
        """Roda em thread. Callbacks de UI (on_progress/on_error) devem ser
        marshallizados pelo caller (ex.: widget.after(0, ...)) via `marshal`
        para não tocar em Tk fora da main thread. on_done continua sendo
        agendado pelo próprio caller na view. `marshal` é `callable -> callable`;
        quando ausente, os callbacks são invocados direto (uso off-UI)."""
        marshal = marshal or (lambda fn: fn)

        def worker():
            dados_temp = {}
            total = len(self.state.placeholders)
            for i, ph in enumerate(self.state.placeholders):
                if ph in self.state.mapeamento:
                    dados = self.state.mapeamento[ph]
                    try:
                        if dados['documento_tipo'] == 'pdf':
                            imagem = pdf_para_imagem(dados['documento_path'])
                        elif dados['documento_tipo'] == 'heic':
                            imagem = heic_para_imagem(dados['documento_path'])
                        else:
                            imagem = Image.open(dados['documento_path'])
                        texto = extrair_texto_do_recorte(imagem, dados)
                        dados_temp[ph] = texto if texto else ""
                    except Exception as e:
                        if on_error:
                            err = str(e)
                            marshal(lambda ph=ph, err=err: on_error(ph, err))
                        dados_temp[ph] = ""
                else:
                    dados_temp[ph] = ""
                if on_progress:
                    marshal(lambda i=i, ph=ph, total=total: on_progress(i+1, total, ph))
            if on_done:
                on_done(dados_temp)
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        return t

    def extrair_de_fonte(self, entry):
        doc_path = entry['documento_path']
        dados = {}
        for ph in self.state.placeholders:
            if ph in entry['mapeamento']:
                coords = entry['mapeamento'][ph]
                try:
                    if entry['documento_tipo'] == 'pdf':
                        imagem = pdf_para_imagem(doc_path)
                    elif entry['documento_tipo'] == 'heic':
                        imagem = heic_para_imagem(doc_path)
                    else:
                        imagem = Image.open(doc_path)
                    dados_ocr = {'x1': coords['x1'], 'y1': coords['y1'], 'x2': coords['x2'], 'y2': coords['y2']}
                    texto = extrair_texto_do_recorte(imagem, dados_ocr)
                    dados[ph] = texto if texto else ""
                except Exception:
                    dados[ph] = ""
            else:
                dados[ph] = ""
        return dados
