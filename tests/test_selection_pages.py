"""Composição das páginas e conversão de coordenadas da janela de seleção."""
from PIL import Image

from ui.selection_pages import (
    montar_composto,
    pagina_do_retangulo,
    pagina_em,
    recorte_local,
    retangulo_composto,
)


def _doc(nome, tamanhos):
    paginas = [Image.new('RGB', t, 'white') for t in tamanhos]
    return {
        'caminho': f'/tmp/{nome}',
        'nome': nome,
        'tipo': 'pdf' if len(paginas) > 1 else 'imagem',
        'imagem_original': paginas[0],
        'paginas': paginas,
    }


def test_empilha_paginas_de_varios_documentos():
    composto, layout = montar_composto([
        _doc('a.pdf', [(100, 200), (100, 200)]),
        _doc('b.png', [(80, 100)]),
    ])
    assert composto.width == 100 + 24
    assert len(layout) == 3
    assert [p['pagina'] for p in layout] == [0, 1, 0]
    assert layout[0]['y'] == 12 + 30
    assert layout[1]['y'] == layout[0]['y'] + 200 + 16 + 30
    assert layout[2]['x'] == (124 - 80) // 2
    assert composto.height == layout[2]['y'] + 100 + 12


def test_fallback_quando_documento_nao_tem_paginas():
    doc = {'caminho': '/tmp/x.png', 'nome': 'x.png', 'tipo': 'imagem',
           'imagem_original': Image.new('RGB', (50, 60), 'white')}
    _, layout = montar_composto([doc])
    assert len(layout) == 1
    assert layout[0]['w'] == 50 and layout[0]['h'] == 60


def test_localiza_pagina_pelo_ponto_e_pelo_retangulo():
    _, layout = montar_composto([_doc('a.pdf', [(100, 200), (100, 200)])])
    p1 = layout[0]
    p2 = layout[1]
    assert pagina_em(layout, p1['x'] + 10, p1['y'] + 10) is p1
    assert pagina_em(layout, 0, 0) is None
    assert pagina_do_retangulo(layout, 10, p2['y'] + 10, 40, p2['y'] + 30) is p2


def test_recorte_local_e_retangulo_composto_ida_e_volta():
    _, layout = montar_composto([_doc('a.pdf', [(100, 200)])])
    p = layout[0]
    composto = retangulo_composto(p, 10, 20, 60, 70)
    assert recorte_local(p, composto['x1'], composto['y1'], composto['x2'], composto['y2']) == (10, 20, 60, 70)


def test_recorte_local_clampa_e_rejeita_degenerado():
    _, layout = montar_composto([_doc('a.pdf', [(100, 200)])])
    p = layout[0]
    assert recorte_local(p, p['x'] + 90, p['y'] + 190, p['x'] + 500, p['y'] + 500) == (90, 190, 100, 200)
    assert recorte_local(p, p['x'] + 10, p['y'] + 10, p['x'] + 12, p['y'] + 12) is None
    assert recorte_local(None, 0, 0, 10, 10) is None
