"""
Módulo para ler e escrever arquivos ODT (LibreOffice).

Placeholders são lidos no nível do parágrafo (text:p/text:h), concatenando
todos os nós de texto — inclusive dentro de formas/caixas de texto e mesmo
quando o placeholder é dividido entre spans.
"""

import io
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
import zipfile

NS_TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
TAGS_PARAGRAFO = {f"{{{NS_TEXT}}}p", f"{{{NS_TEXT}}}h"}
PLACEHOLDER_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def _slots_texto(paragrafo):
    """Nós de texto do parágrafo em ordem de leitura: (elemento, atributo)."""
    slots = []

    def percorrer(elem):
        if elem.text:
            slots.append((elem, "text"))
        for filho in elem:
            percorrer(filho)
            if filho.tail:
                slots.append((filho, "tail"))

    percorrer(paragrafo)
    return slots


def _texto_paragrafo(paragrafo):
    return "".join(getattr(elem, attr) for elem, attr in _slots_texto(paragrafo))


def _substituir_em_paragrafo(paragrafo, dados):
    """Troca placeholders no parágrafo preservando os spans existentes.

    O valor herda a formatação do nó onde o placeholder começa. Quando o
    placeholder atravessa spans, o trecho é removido dos demais nós.
    Recalcula os índices a cada troca para suportar vários placeholders no
    mesmo nó de texto.
    """
    alterou = False

    while True:
        slots = _slots_texto(paragrafo)
        if not slots:
            return alterou

        indices = []
        trechos = []
        pos = 0
        for elem, attr in slots:
            texto = getattr(elem, attr)
            indices.append((pos, pos + len(texto), elem, attr))
            trechos.append(texto)
            pos += len(texto)
        completo = "".join(trechos)

        match = next(
            (
                m for m in PLACEHOLDER_RE.finditer(completo)
                if m.group(1).strip() in dados
            ),
            None,
        )
        if not match:
            return alterou

        inicio, fim = match.span()
        valor = str(dados[match.group(1).strip()])
        afetados = [
            (i, s0, e0, elem, attr)
            for i, (s0, e0, elem, attr) in enumerate(indices)
            if s0 < fim and e0 > inicio
        ]
        for i, s0, e0, elem, attr in reversed(afetados):
            texto = getattr(elem, attr)
            ini = max(inicio, s0) - s0
            fim_local = min(fim, e0) - s0
            novo = (
                texto[:ini] + valor + texto[fim_local:]
                if i == afetados[0][0]
                else texto[:ini] + texto[fim_local:]
            )
            setattr(elem, attr, novo)

        if _texto_paragrafo(paragrafo) == completo:
            return alterou
        alterou = True


def _parse_content(raw):
    for _evento, (prefixo, uri) in ET.iterparse(
        io.BytesIO(raw), events=("start-ns",)
    ):
        ET.register_namespace(prefixo, uri)
    return ET.fromstring(raw)


def _extrair_cru(raw):
    """Fallback para content.xml que não é XML válido."""
    texto = raw.decode("utf-8", errors="ignore")
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    placeholders = set()
    for match in PLACEHOLDER_RE.findall(texto):
        clean = match.strip()
        if 0 < len(clean) <= 80:
            placeholders.add(clean)
    return placeholders


def extrair_placeholders_odt(caminho_odt):
    """Extrai placeholders de todo o content.xml, inclusive dentro de formas."""
    with zipfile.ZipFile(caminho_odt, "r") as odt:
        raw = odt.read("content.xml")

    try:
        root = _parse_content(raw)
    except ET.ParseError:
        return _extrair_cru(raw)

    placeholders = set()
    for elem in root.iter():
        if elem.tag not in TAGS_PARAGRAFO:
            continue
        for match in PLACEHOLDER_RE.findall(_texto_paragrafo(elem)):
            clean = match.strip()
            if 0 < len(clean) <= 80:
                placeholders.add(clean)
    return placeholders


def _substituir_cru(content, dados):
    for placeholder, valor in dados.items():
        safe_valor = (
            str(valor).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        content = content.replace(f"{{{{{placeholder}}}}}", safe_valor)
        content = re.sub(
            r"\{\{\s*" + re.escape(placeholder) + r"\s*\}\}", safe_valor, content
        )
    return content


def gerar_odt_preenchido(caminho_modelo, dados, caminho_saida):
    """
    Gera um novo ODT com os placeholders substituídos
    - Garante mimetype como primeiro arquivo STORED (padrão ODF)
    - Usa ZIP_DEFLATED para demais arquivos
    """
    shutil.copy2(caminho_modelo, caminho_saida)

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(caminho_saida, "r") as odt_in:
            odt_in.extractall(tmpdir)

        content_path = os.path.join(tmpdir, "content.xml")
        with open(content_path, "rb") as f:
            raw = f.read()

        try:
            root = _parse_content(raw)
        except ET.ParseError:
            novo_conteudo = _substituir_cru(raw.decode("utf-8", errors="ignore"), dados)
            with open(content_path, "w", encoding="utf-8") as f:
                f.write(novo_conteudo)
        else:
            for elem in root.iter():
                if elem.tag in TAGS_PARAGRAFO:
                    _substituir_em_paragrafo(elem, dados)
            with open(content_path, "wb") as f:
                f.write(ET.tostring(root, encoding="utf-8", xml_declaration=True))

        # Recria zip com mimetype primeiro
        with zipfile.ZipFile(caminho_saida, "w") as odt_out:
            mimetype_path = os.path.join(tmpdir, "mimetype")
            if os.path.exists(mimetype_path):
                odt_out.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
            for root_dir, _dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    if arcname == "mimetype":
                        continue
                    odt_out.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)
