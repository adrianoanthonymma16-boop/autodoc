"""
Módulo para converter PDF em imagem (todas as páginas ou uma específica)
"""

import contextlib
import os

# Tenta importar pypdfium2
try:
    import pypdfium2 as pdfium
    PDF_SUPORTADO = True
except ImportError:
    PDF_SUPORTADO = False

# Limite de páginas renderizadas para não estourar a memória em PDFs gigantes
MAX_PAGINAS = 30


def _validar(caminho_pdf):
    if not PDF_SUPORTADO:
        raise Exception("Suporte a PDF não disponível. Instale: pip install pypdfium2")
    if not os.path.exists(caminho_pdf):
        raise Exception(f"Arquivo não encontrado: {caminho_pdf}")


def _renderizar(pagina):
    bitmap = pagina.render(scale=2)
    try:
        # copy() desacopla do buffer do pypdfium2, que é liberado no close()
        return bitmap.to_pil().copy()
    finally:
        with contextlib.suppress(Exception):
            bitmap.close()


def pdf_para_imagens(caminho_pdf, limite=MAX_PAGINAS):
    """Converte as páginas de um PDF para imagens PIL (na ordem do documento)."""
    _validar(caminho_pdf)
    pdf = pdfium.PdfDocument(caminho_pdf)
    try:
        total = len(pdf)
        if total == 0:
            raise Exception("PDF vazio")
        return [_renderizar(pdf[i]) for i in range(min(total, limite))]
    finally:
        with contextlib.suppress(Exception):
            pdf.close()


def pdf_para_imagem(caminho_pdf, pagina=0):
    """Converte uma página (índice 0-based) de um PDF para imagem PIL."""
    _validar(caminho_pdf)
    pdf = pdfium.PdfDocument(caminho_pdf)
    try:
        total = len(pdf)
        if total == 0:
            raise Exception("PDF vazio")
        if pagina < 0 or pagina >= total:
            raise Exception(f"Página {pagina + 1} inexistente (PDF tem {total})")
        return _renderizar(pdf[pagina])
    finally:
        with contextlib.suppress(Exception):
            pdf.close()


def pdf_suportado():
    """Retorna True se suporte a PDF está disponível"""
    return PDF_SUPORTADO
