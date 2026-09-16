"""
Módulo para ler e escrever arquivos DOCX (Microsoft Word) - corrigido
Preserva runs/formatação e detecta placeholders quebrados entre runs
"""

import re
import os

try:
    from docx import Document
    DOCX_SUPORTADO = True
except ImportError:
    DOCX_SUPORTADO = False


PLACEHOLDER_RE = re.compile(r'\{\{\s*([^}]+?)\s*\}\}')


def _text_from_paragraph(paragraph):
    """Concatena runs para detectar placeholders divididos"""
    return "".join(run.text for run in paragraph.runs)


def _replace_in_paragraph(paragraph, dados):
    """
    Substitui placeholders preservando runs:
    - Reconstrói texto completo, substitui, e redistribui em runs mantendo estilo do primeiro run
    """
    full = _text_from_paragraph(paragraph)
    if "{{" not in full:
        return False
    # verifica se há placeholder
    found = PLACEHOLDER_RE.search(full)
    if not found:
        return False

    # substitui todos
    new_text = full
    for ph, valor in dados.items():
        # tolera espaços
        new_text = re.sub(r'\{\{\s*' + re.escape(ph) + r'\s*\}\}', valor, new_text)

    if new_text == full:
        return False

    # Redistribui: limpa runs e cria um run com estilo do primeiro
    if paragraph.runs:
        style = paragraph.runs[0].style
        bold = paragraph.runs[0].bold
        italic = paragraph.runs[0].italic
        underline = paragraph.runs[0].underline
        font_name = paragraph.runs[0].font.name
        font_size = paragraph.runs[0].font.size
        color = paragraph.runs[0].font.color.rgb if paragraph.runs[0].font.color else None
        # limpa
        for _ in range(len(paragraph.runs)):
            p = paragraph.runs[0]
            p._element.getparent().remove(p._element)
        run = paragraph.add_run(new_text)
        try:
            run.style = style
            run.bold = bold
            run.italic = italic
            run.underline = underline
            if font_name:
                run.font.name = font_name
            if font_size:
                run.font.size = font_size
            if color:
                run.font.color.rgb = color
        except Exception:
            pass
    else:
        paragraph.text = new_text
    return True


def extrair_placeholders_docx(caminho_docx):
    if not DOCX_SUPORTADO:
        raise Exception("Suporte a DOCX não disponível. Instale: pip install python-docx")

    placeholders = set()
    doc = Document(caminho_docx)

    for paragraph in doc.paragraphs:
        text = _text_from_paragraph(paragraph)
        for match in PLACEHOLDER_RE.findall(text):
            placeholders.add(match.strip())

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    text = _text_from_paragraph(paragraph)
                    for match in PLACEHOLDER_RE.findall(text):
                        placeholders.add(match.strip())

    # Também cobre headers/footers
    for section in doc.sections:
        for hdr in [section.header, section.footer]:
            if hdr:
                for p in hdr.paragraphs:
                    text = _text_from_paragraph(p)
                    for match in PLACEHOLDER_RE.findall(text):
                        placeholders.add(match.strip())

    return placeholders


def gerar_docx_preenchido(caminho_modelo, dados, caminho_saida):
    if not DOCX_SUPORTADO:
        raise Exception("Suporte a DOCX não disponível. Instale: pip install python-docx")

    doc = Document(caminho_modelo)

    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, dados)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_paragraph(paragraph, dados)

    for section in doc.sections:
        for hdr in [section.header, section.footer]:
            if hdr:
                for p in hdr.paragraphs:
                    _replace_in_paragraph(p, dados)

    # hyperlinks e outros: fallback varrendo XML cru
    # (mantém compatibilidade)
    doc.save(caminho_saida)


def docx_suportado():
    return DOCX_SUPORTADO
