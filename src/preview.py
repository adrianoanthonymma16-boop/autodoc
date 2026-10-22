"""
PreviewService - rende o documento gerado (ODT/DOCX) como imagem.

Pipeline: LibreOffice headless converte para PDF; pypdfium2 rasteriza as
primeiras páginas em PNG. Sem LibreOffice, levanta erro amigável.
"""
import os
import shutil
import subprocess
import tempfile

EXTENSOES = (".odt", ".ott", ".docx", ".dotx")
MAX_PAGINAS = 3


def soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def para_pdf(arquivo: str, pasta_saida: str | None = None, timeout: int = 120) -> str:
    exe = soffice()
    if not exe:
        raise RuntimeError(
            "LibreOffice não encontrado. Instale libreoffice para usar a pré-visualização."
        )
    if not os.path.isfile(arquivo):
        raise FileNotFoundError(arquivo)
    destino = pasta_saida or tempfile.mkdtemp(prefix="autodoc-preview-")
    os.makedirs(destino, exist_ok=True)
    subprocess.run(
        [exe, "--headless", "--norestore", "--convert-to", "pdf", "--outdir", destino, arquivo],
        check=True, timeout=timeout,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    pdf = os.path.join(destino, os.path.splitext(os.path.basename(arquivo))[0] + ".pdf")
    if not os.path.isfile(pdf):
        raise RuntimeError("A conversão para PDF não produziu arquivo.")
    return pdf


def paginas_png(pdf: str, pasta_saida: str | None = None,
                max_paginas: int = MAX_PAGINAS, escala: float = 2.0) -> list[str]:
    import pypdfium2 as pdfium

    destino = pasta_saida or tempfile.mkdtemp(prefix="autodoc-preview-")
    os.makedirs(destino, exist_ok=True)
    imagens = []
    doc = pdfium.PdfDocument(pdf)
    try:
        for i in range(min(len(doc), max_paginas)):
            pagina = doc[i]
            bitmap = pagina.render(scale=escala)
            imagem = bitmap.to_pil()
            caminho = os.path.join(destino, f"pagina-{i + 1}.png")
            imagem.save(caminho)
            imagens.append(caminho)
    finally:
        doc.close()
    if not imagens:
        raise RuntimeError("PDF sem páginas.")
    return imagens


def renderizar(arquivo: str, max_paginas: int = MAX_PAGINAS, escala: float = 2.0) -> list[str]:
    """Converte o documento e devolve os PNGs das primeiras páginas."""
    pdf = para_pdf(arquivo)
    return paginas_png(pdf, os.path.dirname(pdf), max_paginas=max_paginas, escala=escala)
