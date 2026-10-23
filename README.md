# AutoDoc &middot; [English](#english)

[![Version](https://img.shields.io/badge/version-4.0.7-blue)](https://github.com/adrianoanthonymma16-boop/autodoc)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-orange)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE.txt)

Automatize o preenchimento de documentos ODT/DOCX usando OCR, planilha ou digitação — **v4.0.7**, com interface premium responsiva, arquitetura desacoplada, lote por planilha, pré-visualização e 100% offline.

---

## Funcionalidades

- **Múltiplos Modelos** — Anexe vários modelos ODT/DOCX; placeholders iguais são unificados automaticamente
- **Lote de Fontes** — Mapeie placeholders em vários documentos-fonte e gere uma saída por fonte
- **Geração Unificada** — Um único botão gera para qualquer combinação (1/N modelos × 1/N fontes)
- **Lote por planilha** — Leia XLSX/CSV/TSV, ajuste o mapeamento das colunas e gere um documento por linha
- **Fichas de dados** — Salve conjuntos de valores (cliente, contrato) e reaplique com um clique
- **Saída organizada** — Pasta padrão, padrão de nome e subpasta por data
- **Pré-visualização** — Veja o documento gerado antes de abrir
- **Confiança de OCR** — Cada campo indica a confiança da leitura e destaca os duvidosos
- **Interface premium (CustomTkinter)** — Sidebar, temas claro/escuro, seletor de arquivos e avisos integrados ao visual
- **Modelos ODT/DOCX** — Placeholders `{{nome}}`, `{{cpf}}`, `{{data}}`
- **Preenchimento Manual** — Digite valores diretamente nos placeholders, sem precisar de OCR
- **OCR Inteligente** — Tesseract com pré-processamento avançado de imagem
- **Biblioteca de Modelos** — Salve e reutilize templates frequentes com um clique
- **Mapeamento Visual** — Janela própria com todas as páginas do documento empilhadas (scroll), OCR e confirmação visível do que já foi mapeado
- **Modo Escuro** — Alternância instantânea com um botão (Ctrl+D)
- **Atalhos de Teclado** — Ctrl+O (modelo), Ctrl+A (anexar), Ctrl+G (gerar), Ctrl+S (salvar), Ctrl+Z (desfazer), Ctrl+E (exportar), Ctrl+I (importar)
- **Zoom e Pan** — Ctrl+Scroll para zoom, botão do meio para arrastar
- **Undo/Redo** — Desfaça e refaça retângulos de mapeamento
- **Validação de Dados** — CPF, data, email e telefone validados automaticamente
- **Exportar/Importar Mapeamento** — Salve e carregue configurações em JSON
- **Backup Automático** — Mapeamento salvo a cada 60 segundos — nunca perca seu trabalho
- **Histórico de Geração** — Registro completo dos documentos gerados
- **Processamento em Lote** — Preencha múltiplos documentos com os mesmos dados (via pasta de modelos)
- **100% Offline** — Sem nuvem, sem internet, seus dados nunca saem da máquina

---

## Requisitos

### Sistema

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk tesseract-ocr tesseract-ocr-por zenity makeself
```

### Python

```bash
pip3 install Pillow opencv-python pytesseract pypdfium2 python-docx ttkbootstrap customtkinter
```

Ou use o script automático:

```bash
bash install_dependencies.sh
```

### Opcional — HEIC (iPhone)

```bash
sudo apt install -y libheif-dev
pip3 install pyheif
```

---

## Uso Rápido

```bash
# Interface ttkbootstrap (original)
python3 run.py

# Interface CustomTkinter (moderna)
python3 run_ctk.py
```

### Fluxo de Trabalho

1. **Modelo** — Carregue um ODT/DOCX com `{{...}}` e/ou anexe mais modelos ao lote
2. **Modelos Salvos** — (opcional) Salve na biblioteca para reuso
3. **Anexar e Mapear** — Anexe fotos/PDFs; a janela de seleção abre sozinha, empilha as páginas e percorre os campos pendentes
4. **Gerar Documento** — Extraia via OCR, revise, gere o(s) documento(s) final(is)
5. **Histórico** — Consulte os documentos gerados anteriormente

---

## Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| `Ctrl+O` | Carregar modelo |
| `Ctrl+A` | Anexar documento |
| `Ctrl+G` | Gerar documento |
| `Ctrl+S` | Salvar mapeamento |
| `Ctrl+Z` | Desfazer retângulo |
| `Ctrl+E` | Exportar mapeamento |
| `Ctrl+I` | Importar mapeamento |
| `Ctrl+D` | Alternar modo escuro/claro |
| `Delete` | Remover retângulo selecionado |
| `Ctrl+Scroll` | Zoom na imagem |
| `Botão Meio + Arrastar` | Mover imagem |

---

## Instalação

> Baixe os instaladores na página [Releases](https://github.com/adrianoanthonymma16-boop/autodoc/releases/latest).
> Os pacotes já incluem o runtime Python — não é preciso instalar Python nem dependências.

### Linux — Snap (Ubuntu e derivados)

```bash
sudo snap install autodoc-ctk
```

O snap já inclui o Tesseract com português e a fonte Inter. Os dados ficam em
`~/snap/autodoc-ctk/common/autodoc`.

### Linux — pacote `.deb` (Ubuntu/Debian)

```bash
# 1. Baixe o .deb da release (ex.: autodoc-ctk_4.0.7_amd64.deb)
# 2. Instale com apt para resolver as dependências do Tesseract:
sudo apt install ./autodoc-ctk_4.0.7_amd64.deb

# 3. Abra pelo menu de aplicativos (AutoDoc) ou pelo terminal:
autodoc-ctk
```

O pacote instala em `/opt/autodoc-ctk`, cria o atalho no menu, e declara
`tesseract-ocr` + `tesseract-ocr-por` como dependências. Se quiser a fonte
da interface, instale também `fonts-inter` (recomendado).

Para remover:

```bash
sudo apt remove autodoc-ctk
```

### Windows 10/11 (64 bits) — instalador `.exe`

1. Baixe `autodoc-ctk_4.0.7_win64_setup.exe` na release.
2. Execute o instalador e siga o assistente (opção de atalho na área de trabalho).
3. Se o SmartScreen avisar, clique em **Mais informações → Executar assim mesmo**.
4. Abra o AutoDoc pelo atalho ou pelo menu Iniciar.

O Tesseract (com o idioma português), a fonte Inter e todas as bibliotecas
Python já vão embutidos no instalador.

### Compilar os instaladores

```bash
# Linux (.deb) — requer Python com requirements.txt, PyInstaller e dpkg-deb
./packaging/build_deb.sh
# saída: dist/autodoc-ctk_<versao>_amd64.deb

# Windows (.exe) — executar no Windows, com Inno Setup 6 e Tesseract instalados
powershell -ExecutionPolicy Bypass -File packaging/windows/build_exe.ps1
# saída: dist/autodoc-ctk_<versao>_win64_setup.exe
```

As releases são geradas automaticamente pelo workflow `.github/workflows/release.yml`
ao publicar uma tag `v*` (ex.: `git tag v4.0.0 && git push origin v4.0.0`).

### Instalador legado `.run` (v3.x)

```bash
bash build_installer_ctk.sh   # gera AutoDocCTk-*.run
chmod +x AutoDocCTk-*.run
./AutoDocCTk-*.run
```

---

## Estrutura do Projeto

### v4.0-premium — Arquitetura Modular (atual)

```
autodoc/
├── run.py                      # Entry legacy ttkbootstrap
├── run_ctk.py                  # Entry premium modular (ui.shell.Shell) com fallback legada
├── instalar.sh                 # Instalador premium (remove antigo, instala novo)
├── iniciar_ctk.sh              # Launcher CTk
├── desinstalar_ctk.sh
├── icon.png
└── src/
    ├── config.py               # VERSAO=4.0-premium
    ├── core/
    │   ├── state.py            # AppState dataclass observável (desacopla UI)
    │   └── bus.py              # EventBus
    ├── services/
    │   ├── modelo.py           # ModeloService (lote, validação)
    │   ├── documento.py        # DocumentoService (PDF/HEIC/IMG)
    │   ├── mapeamento.py       # MapeamentoService (undo/redo, backup atômico)
    │   ├── extracao.py         # ExtracaoService (OCR em thread + confiança)
    │   ├── geracao.py          # GeracaoService
    │   └── planilha.py         # Leitura XLSX/CSV/TSV e mapeamento de colunas
    ├── ui/
    │   ├── theme.py            # Design System LIGHT/DARK + FONTS
    │   ├── shell.py            # Shell: sidebar responsiva + 5 views
    │   ├── canvas/
    │   │   └── image_canvas.py # ImageCanvas (zoom/pan cross-platform, coords corrigidas)
    │   ├── components/
    │   │   └── widgets.py      # card, kpi_card, pill, empty_state, scroll helpers
    │   ├── file_dialog.py      # Seletor de arquivos/pastas no tema do app
    │   ├── messagebox.py       # Avisos e confirmações tematizados
    │   └── views/
    │       ├── modelo_view.py      # KPIs + busca + chips
    │       ├── biblioteca_view.py  # tabela com seleção
    │       ├── mapeamento_view.py  # progress + dual lists + canvas
    │       ├── gerar_view.py       # preview + edição threaded + fichas
    │       ├── lote_view.py        # lote por planilha + relatório
    │       └── historico_view.py
    ├── interface.py            # LEGADO ttkbootstrap 1877 linhas (mantido como fallback)
    ├── interface_ctk.py        # LEGADO CTk monolito 1901 linhas (mantido como fallback)
    ├── fichas.py               # Fichas de dados reutilizáveis
    ├── saida.py                # Nome/pasta de saída (padrões e subpasta por data)
    ├── preview.py              # LibreOffice → PDF → PNG (pypdfium2)
    ├── ocr.py                  # fix RGBA/L/P
    ├── modelo_odt.py           # fix tail/spans + placeholders com "/" e espaço
    ├── modelo_docx.py          # fix runs + placeholders com "/" e espaço
    ├── modelos_salvos.py       # dedup por hash + escrita atômica
    ├── anexo_pdf.py            # try/finally close
    ├── anexo_heic.py           # .copy().convert("RGB")
    └── validadores.py          # filetypes inclui *.heic
```

### Antigo Monolito (v3.9 e anterior) — 1901 linhas inseparáveis

> `src/interface_ctk.py:44` — classe única `AppDocumentosCTK` com ~62 métodos e 50+ atributos em `__init__` (estado + UI acoplados)

```
AppDocumentosCTK (1901 linhas)
├── __init__ (45-103)                     # 50+ atributos misturados
├── _criar_toolbar (109-129) / _criar_abas (135-155) / _configurar_atalhos (161-178) / _alternar_tema (184-192)
├── ABA 1 — Modelo (198-490): _criar_aba_modelo, carregar_modelo (258-327), salvar_modelo_atual, _adicionar_modelo_ao_lote (371-413) com engolir exceção silenciosa, _atualizar_placeholders_unificados, _atualizar_lista_modelos_carregados, _remover_modelo_do_lote
├── ABA 2 — Modelos Salvos (494-667): _criar_aba_modelos_salvos, _atualizar_tabela_modelos_salvos, _selecionar_linha_modelo, _usar_modelo_salvo, _remover_modelo_salvo
├── ABA 3 — Anexar e Mapear (672-1390): dual lists, _bind_zoom_canvas/_zoom/_redesenhar_canvas_com_zoom/_pan (934-980), iniciar/desenhar/finalizar_retangulo (1098-1144) com pan_offset duplo, salvar_mapeamento, _sincronizar_lote_fontes, limpar, _desfazer/_refazer/_remover (1228-1297) com lógica invertida e lote dessincronizado, _exportar/_importar (1303-1390) sem repopular documentos
├── ABA 4 — Gerar (1396-1704): extrair_e_editar_dados (1439-1471) síncrono trava UI, abrir_janela_edicao, salvar_dados_editados, _gerar_documento_unificado (1581-1659)
├── ABA 5 — Historico (1709-1784)
└── Infra (1789-1901): _iniciar_backup/_executar_backup/_tentar_restaurar_backup (backup não-atômico, sem checar arquivo existe)

Estatísticas monolito:
- interface_ctk.py: 1901 linhas, 1 classe, 62 métodos
- interface.py:     1877 linhas, 1 classe, 60 métodos
- Total GUI monolito: ~3778 linhas acopladas, sem testes unitários
```

Principais problemas corrigidos na v4.0 (16 bugs):
`validadores heic` · `undo invertido` · `redo remove` · `lote dessync` · `pan_offset duplo` · `import sem documentos` · `backup fantasma` · `dedup só nome` · `docx perde formatação` · `ocr RGBA/L` · `zoom só Linux` · `odt tail/spans` · `docx runs split` · `OCR trava UI` · `lote engole erro` · `odt mimetype`

---

## Versões

### v4.0.7 (atual) — subpastas no seletor e home real no snap

- **Seletor de modelos/pastas** — a barra lateral "Locais" agora é uma árvore: cada local abre as subpastas em um clique, e a árvore já vem aberta até a pasta atual
- **Início apontava para a pasta errada no snap** — o seletor usava o HOME interno da revisão (`~/snap/autodoc-ctk/<rev>`), então só aparecia "Início" vazio; agora usa `$SNAP_REAL_HOME` e mostra Documentos, Downloads, Imagens e Área de Trabalho de verdade
- **Comportamento fora do snap** — sem `$SNAP_REAL_HOME`, o home continua sendo o do usuário (nenhuma mudança)

### v4.0.6 — placeholders em cabeçalhos, links e revisões

- **DOCX** — placeholders em cabeçalhos/rodapés de primeira página e de páginas pares, dentro de hyperlinks, alterações controladas e controles de conteúdo passam a ser extraídos e preenchidos
- **ODT** — cabeçalhos e rodapés (definidos em `styles.xml`) também entram na extração e no preenchimento
- **Fim do erro falso** — seção sem cabeçalho não gera mais `DOCX: nao foi possivel acessar header` no log
- **Formatação preservada** — a substituição no DOCX ocorre no próprio trecho de texto, sem concentrar o parágrafo em um único run
- **Valores com barra invertida** — caminhos como `C:\temp` deixam de quebrar a geração
- **Janela de mapeamento** — seletor para pular direto a um campo, navegação por página (botões e Page Up/Page Down), destaque do campo atual e botão Remapear no resumo

### v4.0.5 — OCR não perde valores curtos

- Valores curtos lidos pelo OCR ("MG", "SIM", "1") deixam de ser descartados
- Falha do Tesseract agora aparece na janela de seleção com o motivo, e vai para o log
- Segunda tentativa de leitura em escala de cinza e terceira com linha única quando a binarização não lê nada

### v4.0.4 — Seleção com páginas e confirmação visível
- **Lote por planilha** — XLSX/CSV/TSV com sugestão automática de mapeamento e relatório por linha
- **Fichas de dados** e **saída organizada** (pasta padrão, padrão de nome, subpasta por data)
- **Pré-visualização** do documento gerado e **confiança por campo de OCR**
- **Seletor de arquivos e avisos próprios** — mesmo tema do app, com arquivos ocultos fora da lista
- **Correções** — DOCX empacotado sem header/footer, rolagem do preenchimento manual, layout do Lote

### v4.0-premium — Modular + Premium UI
- **Arquitetura desacoplada** — `core/state.py` (AppState observável) + `services/` (modelo, documento, mapeamento, extracao, geracao) + `ui/` (theme, shell, canvas, views) — monolito 1901 linhas → 1403 linhas modulares
- **UI premium responsiva** — sidebar dark `#0F172A` colapsável (<1100px), Design System LIGHT/DARK, KPIs, chips `{{campo}}`, progress bar, cards 16px, empty states
- **Canvas corrigido** — zoom cross-platform (`Ctrl+MouseWheel` + `Ctrl+Button-4/5`), pan `Button-2`/`Shift+drag`, cálculo coords com `pan_x` + escala + clamp
- **16 bugs corrigidos** — heic filetype, undo/redo invertido, lote dessync, pan duplo, import sem docs, backup, dedup hash, docx runs, ocr RGBA, odt tail/spans, OCR thread, pdf leak, etc.
- **OCR não trava** — `ExtracaoService` em thread com barra de progresso
- **Placeholders com `/` e espaço** — `{{PG/NOME GUERRA}}`, `{{PG/NOME_COMPLETO}}` agora detectados (regex `[^}]+`)
- **Biblioteca robusta** — hash SHA256 + escrita atômica, fallback visual corrigido (`border_color transparent` → `c["border"]`)
- **Instalador premium** — `instalar.sh` remove `autodoc.desktop` obsoleto, recria `autodoc-ctk.desktop` v4.0

### v3.9
- **Múltiplos modelos** — Botões "Anexar Individualmente" e "Anexar Vários" na aba Modelo
- **Placeholders unificados** — Placeholders iguais entre modelos são mesclados automaticamente
- **Lote de fontes** — Mapeie placeholders em vários documentos-fonte e gere uma saída por fonte
- **Geração unificada** — Um único botão "Gerar Documento" cobre todos os cenários (1/N modelos × 1/N fontes)
- **Bug fix** — `documento_tipo` agora armazenado por retângulo individual (corrige extração OCR com múltiplos tipos de documento)
- **Persistência** — `modelos` e `lote_fontes` incluídos em backup/restore e export/import JSON

### v3.8
- **Interface CustomTkinter** — Nova GUI com visual moderno, scrollframes interativos e tema escuro/claro nativo
- **Instalador duplo** — Instale e use ambas as interfaces lado a lado (ttkbootstrap + CustomTkinter)
- **Preenchimento manual de placeholders** — Digite valores diretamente sem precisar de OCR ou documentos anexados
- `run_ctk.py` — Entry point para a interface CustomTkinter
- Scripts de build/install/desinstalar específicos para cada interface
- Nova dependência: `customtkinter >= 5.2.0`

### v3.7
- Preenchimento manual de placeholders (botão na aba Gerar)
- Correções e melhorias nos instaladores

### v3.6
- Modo escuro com botão interativo (Ctrl+D)
- Atalhos de teclado para todas as operações principais
- Zoom (Ctrl+Scroll) e Pan (botão do meio) no canvas
- Undo/Redo de retângulos
- Validação automática de CPF, data, email e telefone
- Exportar/Importar mapeamento em JSON
- Backup automático do mapeamento a cada 60 segundos
- Histórico de documentos gerados (nova aba)
- Processamento em lote de múltiplos modelos
- Persistência de preferências (tema, tamanho da janela, último diretório)
- Arquivos de projeto: requirements.txt, .editorconfig, .gitattributes, SECURITY.md, CHANGELOG.md
- GitHub Issue Templates (bug report, feature request)
- Sistema de logging em arquivo
- Módulo de internacionalização preparado
- Nova dependência: `ttkbootstrap`

### v3.5
- Interface moderna com **ttkbootstrap** (tema Cosmo)
- **Biblioteca de Modelos Salvos** — salve e reutilize templates
- Nova aba "Modelos Salvos" com tabela interativa
- Janela maior (1280x820), componentes estilizados
- Módulo `src/modelos_salvos.py`

### v3.4 (branch [`v3.4-legacy`](https://github.com/adrianoanthonymma16-boop/autodoc/tree/v3.4-legacy))
- Interface tkinter tradicional
- Fluxo: Modelo → Anexar e Mapear (OCR) → Gerar Documento
- Suporte a ODT, DOCX, PDF, HEIC e imagens

---

## Contato

Adriano Anthony Jesus Azulay de Araujo  
E-mail: adrianoanthonymma16@gmail.com

---

## Licença

Software de código aberto sob a licença MIT. Veja o arquivo [LICENSE.txt](LICENSE.txt) para os termos completos.

<br>
<hr>
<br>

<a id="english"></a>

# AutoDoc &middot; [Português](#autodoc)

[![Version](https://img.shields.io/badge/version-4.0.7-blue)](https://github.com/adrianoanthonymma16-boop/autodoc)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-orange)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE.txt)

Automate ODT/DOCX document filling using OCR, spreadsheets or manual input — **v4.0.7**, with a premium responsive UI, decoupled architecture, spreadsheet batch, preview and fully offline operation.

---

## Features

- **Multiple Templates** — Load several ODT/DOCX templates; identical placeholders are auto-merged
- **Batch Sources** — Map placeholders across multiple source documents and generate one output per source
- **Unified Generation** — Single button generates for any combination (1/N templates × 1/N sources)
- **Spreadsheet batch** — Read XLSX/CSV/TSV, adjust the column mapping and generate one document per row
- **Data profiles** — Save sets of values (client, contract) and reapply them in one click
- **Organized output** — Default folder, filename pattern and optional date subfolder
- **Preview** — Render the generated document before opening it
- **OCR confidence** — Each field shows the reading confidence and highlights doubtful ones
- **Premium UI (CustomTkinter)** — Sidebar, light/dark themes, themed file picker and dialogs
- **ODT/DOCX Templates** — Placeholders `{{name}}`, `{{cpf}}`, `{{date}}`
- **Manual Filling** — Type values directly into placeholders, no OCR needed
- **Smart OCR** — Tesseract with advanced image pre-processing
- **Template Library** — Save and reuse frequent templates with one click
- **Visual Mapping** — Dedicated window with every document page stacked (scroll), OCR and visible confirmation of mapped fields
- **Dark Mode** — Instant toggle with a button (Ctrl+D)
- **Keyboard Shortcuts** — Ctrl+O (template), Ctrl+A (attach), Ctrl+G (generate), Ctrl+S (save), Ctrl+Z (undo), Ctrl+E (export), Ctrl+I (import)
- **Zoom and Pan** — Ctrl+Scroll to zoom, middle button to drag
- **Undo/Redo** — Undo and redo mapping rectangles
- **Data Validation** — CPF, date, email and phone validated automatically
- **Export/Import Mapping** — Save and load configurations in JSON
- **Automatic Backup** — Mapping saved every 60 seconds — never lose your work
- **Generation History** — Complete log of generated documents
- **Batch Processing** — Fill multiple documents with the same data (via template folder)
- **100% Offline** — No cloud, no internet, your data never leaves the machine

---

## Requirements

### System

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-tk tesseract-ocr tesseract-ocr-por zenity makeself
```

### Python

```bash
pip3 install Pillow opencv-python pytesseract pypdfium2 python-docx ttkbootstrap customtkinter
```

Or use the automated script:

```bash
bash install_dependencies.sh
```

### Optional — HEIC (iPhone)

```bash
sudo apt install -y libheif-dev
pip3 install pyheif
```

---

## Quick Start

```bash
# ttkbootstrap interface (original)
python3 run.py

# CustomTkinter interface (modern)
python3 run_ctk.py
```

### Workflow

1. **Template** — Load an ODT/DOCX with `{{...}}` and/or attach more templates to the batch
2. **Saved Templates** — (optional) Save to library for reuse
3. **Attach and Map** — Attach photos/PDFs, draw rectangles on fields (supports batch sources)
4. **Generate Document** — Extract via OCR, review, generate the final document(s)
5. **History** — Browse previously generated documents

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Load template |
| `Ctrl+A` | Attach document |
| `Ctrl+G` | Generate filled document |
| `Ctrl+S` | Save mapping |
| `Ctrl+Z` | Undo rectangle |
| `Ctrl+E` | Export mapping |
| `Ctrl+I` | Import mapping |
| `Ctrl+D` | Toggle dark/light mode |
| `Delete` | Remove selected rectangle |
| `Ctrl+Scroll` | Zoom image |
| `Middle Button + Drag` | Pan image |

---

## Install

> Download the installers from [Releases](https://github.com/adrianoanthonymma16-boop/autodoc/releases/latest).
> They bundle the Python runtime — no Python or pip install needed.

### Linux — Snap (Ubuntu and derivatives)

```bash
sudo snap install autodoc-ctk
```

The snap bundles Tesseract with Portuguese and the Inter font. Data lives in
`~/snap/autodoc-ctk/common/autodoc`.

### Linux — `.deb` (Ubuntu/Debian)

```bash
sudo apt install ./autodoc-ctk_4.0.7_amd64.deb
autodoc-ctk
```

### Windows 10/11 (64-bit) — `.exe`

1. Download `autodoc-ctk_4.0.7_win64_setup.exe`.
2. Run the wizard (optionally create a desktop shortcut).
3. If SmartScreen warns, choose **More info → Run anyway**.

### Build the installers

```bash
./packaging/build_deb.sh                                  # Linux
powershell -File packaging/windows/build_exe.ps1          # Windows
```

---

## Project Structure

```
autodoc/
├── run.py                      # Entry legacy ttkbootstrap
├── run_ctk.py                  # Entry premium modular (ui.shell.Shell) + fallback
├── instalar.sh                 # Instalador premium v4.0
├── iniciar_ctk.sh              # Launcher CTk
├── desinstalar_ctk.sh
├── src/
│   ├── config.py               # VERSAO=4.0-premium
│   ├── core/state.py + bus.py
│   ├── services/{modelo,documento,mapeamento,extracao,geracao,planilha}.py
│   ├── ui/{theme,shell,canvas/image_canvas,components/widgets,file_dialog,messagebox,views/*}.py
│   ├── {fichas,saida,preview}.py
│   ├── interface.py            # LEGADO 1877 linhas
│   └── interface_ctk.py        # LEGADO 1901 linhas
```

---

## Versions

### v4.0.7 (current) — subfolders in the picker and real home in the snap

- **Model/folder picker** — the "Locais" sidebar is now a tree: each location expands its subfolders in one click, and the tree opens down to the current folder
- **Home pointed to the wrong folder in the snap** — the picker used the revision-internal HOME (`~/snap/autodoc-ctk/<rev>`), so only an empty "Início" appeared; it now uses `$SNAP_REAL_HOME` and shows the real Documents, Downloads, Pictures and Desktop
- **Outside the snap** — without `$SNAP_REAL_HOME`, the user home is unchanged

### v4.0.6 — placeholders in headers, links and revisions

- **DOCX** — placeholders in first-page/even-page headers and footers, inside hyperlinks, tracked changes and content controls are now extracted and filled
- **ODT** — headers and footers (defined in `styles.xml`) are included in extraction and filling
- **No more false error** — a section without a header no longer logs `DOCX: nao foi possivel acessar header`
- **Formatting preserved** — DOCX replacement happens in the text node itself instead of collapsing the paragraph into one run
- **Backslash values** — paths such as `C:\temp` no longer break generation
- **Mapping window** — jump-to-field selector, page navigation (buttons and Page Up/Page Down), highlight of the current field and a Remap button in the summary

### v4.0.5 — OCR keeps short values

- Short OCR results ("MG", "SIM", "1") are no longer discarded
- Tesseract failures now appear in the selection window with the actual reason and are written to the log
- Second read attempt in grayscale and a third with single-line segmentation when binarization finds nothing

### v4.0.4 — Multi-page selection and visible confirmation
- Spreadsheet batch (XLSX/CSV/TSV) with automatic column mapping and per-row report
- Data profiles, organized output and document preview; per-field OCR confidence
- Themed file picker and dialogs; hidden dotfiles stay out of the list
- Fixes: packaged DOCX without header/footer, manual-fill scrolling, batch layout

### v4.0-premium — Modular + Premium UI
- Decoupled architecture — `core/state` + `services/` + `ui/` — 1901-line monolith → 1403 modular lines
- Premium responsive UI — dark sidebar collapsible, Design System, KPIs, chips, progress
- Fixed canvas (cross-platform zoom/pan, coords), 16 bugs, threaded OCR, placeholders with `/` and space supported
- Atomic backup, hash dedup, HEIC filetype, RGBA OCR fix

### v3.9
- **Multiple templates** — "Attach Individually" and "Attach Multiple" buttons in the Template tab
- **Unified placeholders** — Identical placeholders across templates are auto-merged
- **Batch sources** — Map placeholders across multiple source documents, one output per source
- **Unified generation** — Single "Generate Document" button covers all scenarios (1/N templates × 1/N sources)
- **Bug fix** — `documento_tipo` now stored per-rectangle (fixes OCR extraction across different document types)
- **Persistence** — `modelos` and `lote_fontes` included in backup/restore and JSON export/import

### v3.8
- **CustomTkinter Interface** — New GUI with modern look, interactive scrollframes and native dark/light theme
- **Dual installer** — Install and use both interfaces side by side (ttkbootstrap + CustomTkinter)
- **Manual placeholder filling** — Type values directly without OCR or attached documents
- `run_ctk.py` — Entry point for the CustomTkinter interface
- Separate build/install/uninstall scripts for each interface
- New dependency: `customtkinter >= 5.2.0`

### v3.7
- Manual placeholder filling (button in the Generate tab)
- Installer fixes and improvements

### v3.6
- Dark mode with interactive button (Ctrl+D)
- Keyboard shortcuts for all main operations
- Zoom (Ctrl+Scroll) and Pan (middle button) on canvas
- Undo/Redo of rectangles
- Automatic CPF, date, email and phone validation
- Export/Import mapping in JSON
- Automatic mapping backup every 60 seconds
- Generated documents history (new tab)
- Batch processing of multiple templates
- Preferences persistence (theme, window size, last directory)
- Project files: requirements.txt, .editorconfig, .gitattributes, SECURITY.md, CHANGELOG.md
- GitHub Issue Templates (bug report, feature request)
- File-based logging system
- Internationalization module prepared
- New dependency: `ttkbootstrap`

### v3.5
- Modern interface with **ttkbootstrap** (Cosmo theme)
- **Saved Templates Library** — save and reuse templates
- New "Saved Templates" tab with interactive table
- Larger window (1280x820), styled components
- Module `src/modelos_salvos.py`

### v3.4 (branch [`v3.4-legacy`](https://github.com/adrianoanthonymma16-boop/autodoc/tree/v3.4-legacy))
- Traditional tkinter interface
- Flow: Template → Attach and Map (OCR) → Generate Document
- Support for ODT, DOCX, PDF, HEIC and images

---

## Contact

Adriano Anthony Jesus Azulay de Araujo  
E-mail: adrianoanthonymma16@gmail.com

---

## License

Open source software under the MIT license. See [LICENSE.txt](LICENSE.txt) for the full terms.
