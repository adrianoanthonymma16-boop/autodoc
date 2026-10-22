"""Leitura de PDF com várias páginas."""
import pytest
from PIL import Image

from anexo_pdf import PDF_SUPORTADO, pdf_para_imagem, pdf_para_imagens

pytestmark = pytest.mark.skipif(not PDF_SUPORTADO, reason="pypdfium2 indisponível")


def _pdf(tmp_path, paginas=3):
    caminho = tmp_path / "multi.pdf"
    imagens = [Image.new("RGB", (120, 160), "white") for _ in range(paginas)]
    imagens[0].save(caminho, save_all=True, append_images=imagens[1:])
    return str(caminho)


def test_pdf_para_imagens_le_todas_as_paginas(tmp_path):
    imagens = pdf_para_imagens(_pdf(tmp_path, 3))
    assert len(imagens) == 3
    assert imagens[0].width == 240 and imagens[0].height == 320


def test_pdf_para_imagem_por_indice(tmp_path):
    pagina = pdf_para_imagem(_pdf(tmp_path, 2), 1)
    assert pagina.width == 240


def test_pdf_pagina_inexistente(tmp_path):
    with pytest.raises(Exception, match="inexistente"):
        pdf_para_imagem(_pdf(tmp_path, 2), 5)
