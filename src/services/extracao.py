"""
ExtracaoService - OCR em thread para não congelar UI
"""
import threading

from PIL import Image

from anexo_heic import heic_para_imagem
from anexo_pdf import pdf_para_imagem
from ocr import extrair_recorte_com_confianca


class ExtracaoService:
    def __init__(self, state):
        self.state = state

    @staticmethod
    def _imagem_documento(doc_path, doc_tipo, pagina=0):
        """Carrega a página certa do documento fonte (PDF multi-página)."""
        if doc_tipo == 'pdf':
            return pdf_para_imagem(doc_path, pagina)
        if doc_tipo == 'heic':
            return heic_para_imagem(doc_path)
        return Image.open(doc_path)

    def extrair_todos(self, on_progress=None, on_done=None, on_error=None, marshal=None):
        """Roda em thread. Callbacks de UI (on_progress/on_error) devem ser
        marshallizados pelo caller (ex.: widget.after(0, ...)) via `marshal`
        para não tocar em Tk fora da main thread. on_done continua sendo
        agendado pelo próprio caller na view. `marshal` é `callable -> callable`;
        quando ausente, os callbacks são invocados direto (uso off-UI)."""
        marshal = marshal or (lambda fn: fn)

        def worker():
            dados_temp = {}
            conf_temp = {}
            total = len(self.state.placeholders)
            for i, ph in enumerate(self.state.placeholders):
                if ph in self.state.mapeamento:
                    dados = self.state.mapeamento[ph]
                    try:
                        imagem = self._imagem_documento(
                            dados['documento_path'],
                            dados['documento_tipo'],
                            dados.get('pagina', 0),
                        )
                        texto, conf = extrair_recorte_com_confianca(imagem, dados)
                        dados_temp[ph] = texto if texto else ""
                        conf_temp[ph] = conf if texto else 0.0
                    except Exception as e:
                        if on_error:
                            err = str(e)
                            marshal(lambda ph=ph, err=err: on_error(ph, err))
                        dados_temp[ph] = ""
                        conf_temp[ph] = 0.0
                else:
                    dados_temp[ph] = ""
                    conf_temp[ph] = None
                if on_progress:
                    marshal(lambda i=i, ph=ph, total=total: on_progress(i+1, total, ph))
            if on_done:
                on_done(dados_temp, conf_temp)
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
                    imagem = self._imagem_documento(
                        doc_path, entry['documento_tipo'], coords.get('pagina', 0)
                    )
                    dados_ocr = {'x1': coords['x1'], 'y1': coords['y1'], 'x2': coords['x2'], 'y2': coords['y2']}
                    texto, _conf = extrair_recorte_com_confianca(imagem, dados_ocr)
                    dados[ph] = texto if texto else ""
                except Exception:
                    dados[ph] = ""
            else:
                dados[ph] = ""
        return dados
