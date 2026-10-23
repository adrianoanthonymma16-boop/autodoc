# Changelog

All notable changes to this project will be documented in this file.

## [4.0.5] - 2026-10-23

### Fixed
- **OCR descartava valores curtos** — leituras como "MG", "SIM" ou "1" eram tratadas como vazio e o campo aparecia como não lido; agora qualquer texto lido é preservado
- **OCR silencioso** — quando o Tesseract falha, a janela de seleção mostra o motivo real em vez de apenas "Nada foi lido nesta área", e o erro fica registrado no log
- **Leitura em digitalizações difíceis** — se a binarização não encontra texto, o OCR tenta a região em escala de cinza e, por último, segmentação de linha única
- **Idioma indisponível** — se o pacote de português do Tesseract não estiver instalado, usa inglês em vez de falhar

## [4.0.4] - 2026-10-22

### Fixed
- **Janela de seleção ao anexar** — o documento anexado abre automaticamente a janela separada de mapeamento
- **PDF com várias páginas** — todas as páginas são empilhadas com rolagem vertical; o próximo documento anexado continua no mesmo scroll
- **Confirmação visível** — campo com valor confirmado mostra check verde e o selo "confirmado" na lista (e "mapeado" quando ainda não tem valor)
- **Página no mapeamento** — cada recorte guarda a página de origem, e a extração OCR usa a página correta
- **Retângulos de referência** — os mapeamentos já confirmados aparecem na janela com o nome do campo e contador de confirmados

## [4.0.3] - 2026-10-22

### Added
- **Seleção visual em janela própria** — o documento inteiro é exibido para escolher a área, com OCR do recorte e confirmação/edição do valor antes de salvar
- **Salvar e próximo campo** — percorre os campos pendentes do mesmo documento sem reabrir a janela, mantendo os retângulos já confirmados como referência e mostrando um resumo ao final
- **Lista de mapeamentos clicável** — mostra campo, documento e valor confirmado; clicar na linha reabre a seleção para remapear

### Changed
- A aba Mapear perdeu o canvas de seleção do rodapé; a seleção acontece só na janela e a lista de mapeamentos ocupa a área principal
- Duplo clique em um documento abre direto a janela de seleção para o campo escolhido

## [4.0.2] - 2026-10-22

### Added
- **Lote por planilha** — aba Lote lê XLSX/CSV/TSV, sugere o mapeamento das colunas e gera um documento por linha, com relatório de erros
- **Fichas de dados** — salve conjuntos de valores e reaplique na revisão ou no preenchimento manual
- **Saída organizada** — pasta padrão, padrão de nome (`{modelo}`, `{indice}`, `{data}`) e subpasta por data
- **Pré-visualização** — converte o documento gerado em imagem (LibreOffice + PDF) antes de abrir
- **Confiança de OCR** — cada campo mostra a confiança da leitura e destaca os duvidosos
- **Seletor de arquivos próprio** — no tema do app, com locais rápidos, filtros e arquivos com "." ocultos
- **Avisos e confirmações próprios** — diálogos tematizados no lugar dos messageboxes do Tk
- **Seleção visual com confirmação** — a área do campo é escolhida em janela própria com o documento inteiro; o OCR mostra o valor extraído para confirmar ou editar antes de salvar
- **Snap** — pacote publicado na Snap Store

### Fixed
- DOCX no binário empacotado falhava ao abrir modelos sem cabeçalho/rodapé (`default-header.xml`)
- Rolagem do preenchimento manual não funcionava sobre os campos de texto
- Aba Lote com mapeamento em duas colunas e ações sempre visíveis
- Barra de rolagem invisível em painéis escuros
- Geração e extração não travam mais a interface (threads com retorno para a UI)
- Placeholders dentro de formas (caixas de texto) do DOCX e do ODT agora são detectados e preenchidos

## [3.9.0] - 2026-07-14

### Added
- **Múltiplos modelos** — Botões "Anexar Individualmente" e "Anexar Vários" na aba Modelo
- **Placeholders unificados** — Placeholders iguais entre modelos são mesclados automaticamente
- **Lote de fontes** — Estrutura `self.lote_fontes` para mapear placeholders em vários documentos-fonte
- **Geração unificada** — Único botão "Gerar Documento" (Ctrl+G) cobre todos os cenários
- **Lista de modelos carregados** — Exibe modelos, placeholders e botão remover
- **Backup/Restore e Export/Import** — Incluem `modelos` e `lote_fontes`

### Fixed
- **Bug: `documento_tipo`** — Agora armazenado por retângulo (`finalizar_retangulo`), corrigindo OCR com múltiplos tipos de documento anexados

### Removed
- Botão "Gerar Documento Preenchido", "Gerar em Lote (Modelos)" e "Gerar Lote de Documentos" substituídos por um único "Gerar Documento"

## [3.8.0] - 2026-07-13

### Added
- Interface CustomTkinter com visual moderno (`interface_ctk.py`, `run_ctk.py`)
- CTkScrollableFrame para listas, CTkCanvas para desenho
- Temas Light/Dark nativos via `set_appearance_mode()`
- Instalador duplo — ambas interfaces podem coexistir (ttkbootstrap + CustomTkinter)
- Preenchimento manual de placeholders (digitação direta sem OCR)

## [3.7.0] - 2026-07-02

### Added
- Preenchimento manual de placeholders (botão na aba Gerar)
- Correções nos instaladores

## [3.6.0] - 2026-07-02

### Added
- Dark mode with interactive toggle button
- Keyboard shortcuts (Ctrl+O, Ctrl+A, Ctrl+G, Ctrl+S, Ctrl+Z, Delete)
- Canvas zoom (mouse wheel) and pan (drag)
- Drag & drop file support for models and attachments
- Undo/Redo for rectangle drawings
- Data validation for CPF, dates, and emails during editing
- Batch document generation
- Export/Import mapping configurations (JSON)
- Document preview in generation tab
- Automatic backup of mapping state
- Application logging system (~/.autodoc/app.log)
- Generation history tracking
- User preferences persistence (window size, last directory, theme)
- Project files: requirements.txt, .editorconfig, .gitattributes, SECURITY.md
- GitHub issue templates (bug report, feature request)
- Internationalization module prepared for future translations

### Changed
- Version bumped to 3.6.0
- Theme toggle between light (cosmo) and dark (cyborg)
- Improved window behavior — remembers size/position across sessions

## [3.5.0] - 2026-07-02

### Added
- Modern interface with ttkbootstrap (Cosmo theme)
- Model library — save and reuse templates without re-uploading
- New "Saved Models" tab with interactive table
- New module src/modelos_salvos.py for model persistence

### Changed
- Larger window (1280x820)
- Better styled components with Helvetica font
- Improved usability throughout all tabs

## [3.4.0] - 2026-07-01

### Added
- Initial release
- ODT/DOCX template support
- OCR via Tesseract with image preprocessing
- Document attachment (JPG, PNG, PDF, TIFF, HEIC, WEBP)
- Rectangle drawing for field mapping
- ODT/DOCX generation with placeholder replacement
- Traditional tkinter interface
