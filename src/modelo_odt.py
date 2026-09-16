"""
Módulo para ler e escrever arquivos ODT (LibreOffice) - corrigido
"""

import re
import zipfile
import xml.etree.ElementTree as ET
import shutil
import tempfile
import os


def _texto_completo_odt(root):
    """Extrai texto concatenando text + tail de todos elementos, detecta placeholders mesmo quebrados em spans"""
    textos = []
    for elem in root.iter():
        if elem.text:
            textos.append(elem.text)
        if elem.tail:
            textos.append(elem.tail)
    return " ".join(textos)


def extrair_placeholders_odt(caminho_odt):
    """
    Extrai todos os placeholders {{...}} de um arquivo ODT
    - Lê content.xml inteiro como texto para capturar tail e quebras de tag
    - Usa regex no XML cru antes de parsear para capturar placeholders divididos entre tags
    """
    placeholders = set()

    with zipfile.ZipFile(caminho_odt, 'r') as odt:
        raw = odt.read('content.xml').decode('utf-8', errors='ignore')
        # Remove tags mas mantém espaço para não colar palavras
        without_tags = re.sub(r'<[^>]+>', ' ', raw)
        # Normaliza whitespace de split
        without_tags = re.sub(r'\s+', ' ', without_tags)
        # Captura {{ }} mesmo com espaços
        for match in re.findall(r'\{\{\s*([^}]+?)\s*\}\}', without_tags):
            clean = match.strip()
            if 0 < len(clean) <= 80:
                placeholders.add(clean)

        # Fallback estruturado via iter (caso regex falhe em edge)
        try:
            with odt.open('content.xml') as content:
                tree = ET.parse(content)
                root = tree.getroot()
                completo = _texto_completo_odt(root)
                for match in re.findall(r'\{\{\s*([^}]+?)\s*\}\}', completo):
                    clean = match.strip()
                    if 0 < len(clean) <= 80:
                        placeholders.add(clean)
        except Exception:
            pass

    return placeholders


def gerar_odt_preenchido(caminho_modelo, dados, caminho_saida):
    """
    Gera um novo ODT com os placeholders substituídos
    - Garante mimetype como primeiro arquivo STORED (padrão ODF)
    - Usa ZIP_DEFLATED para demais arquivos
    """
    shutil.copy2(caminho_modelo, caminho_saida)

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(caminho_saida, 'r') as odt_in:
            odt_in.extractall(tmpdir)

        content_path = os.path.join(tmpdir, 'content.xml')
        with open(content_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for placeholder, valor in dados.items():
            # Escape XML básico no valor
            safe_valor = valor.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Usamos placeholder cru entre chaves, mas substituímos ambas variações
            content = content.replace(f"{{{{{placeholder}}}}}", safe_valor)
            # Também tolera espaços internos {{ placeholder }}
            content = re.sub(r'\{\{\s*' + re.escape(placeholder) + r'\s*\}\}', safe_valor, content)

        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Recria zip com mimetype primeiro
        with zipfile.ZipFile(caminho_saida, 'w') as odt_out:
            mimetype_path = os.path.join(tmpdir, 'mimetype')
            if os.path.exists(mimetype_path):
                odt_out.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            for root_dir, dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    if arcname == 'mimetype':
                        continue
                    odt_out.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)
