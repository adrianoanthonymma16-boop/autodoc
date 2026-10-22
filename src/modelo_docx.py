"""
Módulo para ler e escrever arquivos DOCX (Microsoft Word) - corrigido
Preserva runs/formatação e detecta placeholders quebrados entre runs
"""

import re

try:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
    DOCX_SUPORTADO = True
except ImportError as _e:
    DOCX_SUPORTADO = False
    try:
        from logger import log_erro
        log_erro(f"Falha ao importar python-docx: {_e}")
    except Exception:
        pass


PLACEHOLDER_RE = re.compile(r'\{\{\s*([^}]+?)\s*\}\}')


def _partes_cabecalho_rodape(section):
    """Acessa header/footer com tolerância.

    Em builds congelados (PyInstaller) o python-docx pode não achar o template
    default-header.xml ao criar uma seção sem cabeçalho; nesse caso o documento
    ainda deve carregar (só os placeholders de cabeçalho/rodapé ficam de fora).
    """
    partes = []
    for attr in ("header", "footer"):
        try:
            partes.append(getattr(section, attr))
        except Exception as e:
            try:
                from logger import log_erro
                log_erro(f"DOCX: nao foi possivel acessar {attr}: {e}")
            except Exception:
                pass
    return partes


def _paragrafos_recursivos(raiz, pai):
    """Percorre todos os w:p do XML, inclusive dentro de formas e controles.

    python-docx só expõe os parágrafos do corpo/tabelas/cabeçalhos; textos
    dentro de caixas de texto (w:txbxContent) e controles de conteúdo
    (w:sdtContent) ficam de fora. Aqui varremos o XML e reaproveitamos a
    mesma lógica de runs/estilo.
    """
    if raiz is None:
        return
    for elemento in raiz.iter(qn("w:p")):
        yield Paragraph(elemento, pai)


def _paragrafos_documento(doc):
    """Parágrafos do corpo (formas, controles, tabelas) e cabeçalhos/rodapés."""
    yield from _paragrafos_recursivos(doc.element.body, doc)

    for section in doc.sections:
        for parte in _partes_cabecalho_rodape(section):
            if parte is not None:
                yield from _paragrafos_recursivos(parte._element, parte)


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

    # Redistribui: limpa apenas runs de texto, preservando desenhos/formas
    # ancorados no mesmo parágrafo.
    runs_texto = [r for r in paragraph.runs if r.text]
    if runs_texto:
        base = runs_texto[0]
        style = base.style
        bold = base.bold
        italic = base.italic
        underline = base.underline
        font_name = base.font.name
        font_size = base.font.size
        color = base.font.color.rgb if base.font.color else None
        for r in runs_texto:
            r._element.getparent().remove(r._element)
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

    for paragraph in _paragrafos_documento(doc):
        text = _text_from_paragraph(paragraph)
        for match in PLACEHOLDER_RE.findall(text):
            placeholders.add(match.strip())

    return placeholders


def gerar_docx_preenchido(caminho_modelo, dados, caminho_saida):
    if not DOCX_SUPORTADO:
        raise Exception("Suporte a DOCX não disponível. Instale: pip install python-docx")

    doc = Document(caminho_modelo)

    for paragraph in _paragrafos_documento(doc):
        _replace_in_paragraph(paragraph, dados)

    doc.save(caminho_saida)


def docx_suportado():
    return DOCX_SUPORTADO
