"""
Composição das páginas dos documentos para a janela de seleção.

Empilha as páginas de todos os documentos anexados numa única imagem,
com faixa de cabeçalho por página, e converte coordenadas entre a imagem
composta (canvas) e a página local (onde o recorte é salvo).
"""

from PIL import Image, ImageDraw

CABECALHO = 30
ESPACO = 16
MARGEM = 12
FUNDO = (226, 232, 240)
BORDA = (148, 163, 184)


def paginas_de(documento):
    """Páginas de um documento, com fallback para o campo antigo."""
    return documento.get('paginas') or [documento['imagem_original']]


def montar_composto(documentos, cabecalho=CABECALHO, espaco=ESPACO, margem=MARGEM):
    """Empilha as páginas e devolve (imagem_composta, lista_de_paginas)."""
    paginas = [p for doc in documentos for p in paginas_de(doc)]
    if not paginas:
        raise ValueError("Nenhuma página para exibir")

    largura = max(p.width for p in paginas) + margem * 2
    altura = sum(p.height + cabecalho for p in paginas) + espaco * (len(paginas) - 1) + margem * 2
    composto = Image.new('RGB', (largura, altura), FUNDO)
    desenho = ImageDraw.Draw(composto)

    layout = []
    y = margem
    for doc in documentos:
        for indice, pagina in enumerate(paginas_de(doc)):
            x = (largura - pagina.width) // 2
            topo = y + cabecalho
            composto.paste(pagina, (x, topo))
            desenho.rectangle(
                [x - 1, topo - 1, x + pagina.width, topo + pagina.height],
                outline=BORDA,
            )
            layout.append({
                'documento_path': doc['caminho'],
                'documento_nome': doc.get('nome', ''),
                'documento_tipo': doc.get('tipo', 'imagem'),
                'pagina': indice,
                'total_paginas': len(paginas_de(doc)),
                'x': x,
                'y': topo,
                'w': pagina.width,
                'h': pagina.height,
                'imagem': pagina,
            })
            y = topo + pagina.height + espaco
    return composto, layout


def pagina_em(paginas, x, y):
    """Página que contém o ponto (coordenadas do composto), ou None."""
    for p in paginas:
        if p['x'] <= x <= p['x'] + p['w'] and p['y'] <= y <= p['y'] + p['h']:
            return p
    return None


def pagina_do_retangulo(paginas, x1, y1, x2, y2):
    """Página com maior sobreposição vertical com o retângulo."""
    melhor, area = None, 0
    for p in paginas:
        topo = max(y1, p['y'])
        base = min(y2, p['y'] + p['h'])
        sobreposicao = max(0, base - topo)
        if sobreposicao > area:
            melhor, area = p, sobreposicao
    return melhor


def recorte_local(pagina, x1, y1, x2, y2):
    """Converte um retângulo do composto em coordenadas locais da página."""
    if pagina is None:
        return None
    lx1 = max(0, min(int(x1) - pagina['x'], pagina['w']))
    ly1 = max(0, min(int(y1) - pagina['y'], pagina['h']))
    lx2 = max(0, min(int(x2) - pagina['x'], pagina['w']))
    ly2 = max(0, min(int(y2) - pagina['y'], pagina['h']))
    if lx2 - lx1 < 4 or ly2 - ly1 < 4:
        return None
    return lx1, ly1, lx2, ly2


def retangulo_composto(pagina, x1, y1, x2, y2):
    """Converte coordenadas locais da página para o composto."""
    return {
        'x1': pagina['x'] + x1,
        'y1': pagina['y'] + y1,
        'x2': pagina['x'] + x2,
        'y2': pagina['y'] + y2,
    }
