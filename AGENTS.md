# AGENTS.md — Diretrizes do projeto AutoDoc-CTk

## 1. Ícones: nunca emojis, sempre SVG

- **Proibido emoji colorido** em qualquer string visível da interface nova
  (`src/ui/**`, `src/mensagens.py`): sem 📄 📚 🎯 ✨ 🕘 🌙 ☀️ 💾 🔍 ✏️ 🚀 ✅ ⚠️ 📂 📭 🖼️,
  sem setas textuais especiais (↻ ↩), sem fullwidth (＋ －) e sem
  circled numbers (① ② ③ ④). Motivo: emoji força fallback para fonte
  bitmap colorida (lenta, gigante no layout) e quebra entre temas.
- **Fonte única de verdade: `assets/icons/*.svg`** (stroke 24×24,
  `stroke="currentColor"`). Não criar pictograma por outro meio.
- **Render via `src/ui/icons.py`**: `get(nome, tamanho, cor_hex)` retorna
  `CTkImage` com cache; `render()` é puro (PIL, sem Tk) e testável.
  Registrar nomes novos em `ICONS` e cobrir em `tests/test_icons.py`.
- **Exceção narrow**: glifos de texto inline `✓ ○ → • ◆` são permitidos
  **apenas** como prefixo de status em linhas de lista/labels — são glifos
  da fonte Inter (rápidos), não emoji. Todo o resto pictórico é SVG.
- Escopo: a regra vale para o app novo (`run_ctk.py` → `ui/shell.py`).
  `src/interface.py` e `src/interface_ctk.py` são legado em migração
  (fallback) e estão fora do escopo até a remoção.

## 2. Performance da UI (CustomTkinter é caro por widget)

Medido em máquina lenta: construir as 5 views de uma vez custava ~55 s
de startup; rebuild total por troca/toggle ~35–40 s. Regras:

- **Lazy views**: `Shell` só constrói a view visível (`_ensure_view`).
  Nunca instanciar todas no `__init__`.
- **Dirty-flag, nunca rebuild incondicional**: view expõe `_dirty` e
  `refresh_view()`; `Shell._switch` só reconstrói se dirty. Listas com
  dados externos usam **assinatura** (ex.: tupla de campos + query de
  busca) e retornam cedo se nada mudou.
- **Toggle de tema é barato**: recolore shell + view atual; demais views
  construídas recebem `_dirty = True` (rebuild lazy na próxima visita).
  Não chamar `_refresh`/`refresh` em todas as views.
- **Busca com debounce** (`after(200)`, cancela pendente): nunca rebuild
  por `KeyRelease` direto.
- **`<Configure>` borbulha dos filhos**: filtrar pelo path Tk da janela
  (`_w`) **e** debounce com `after(120)`; handler idempotente.
- **Medir antes de otimizar**: smoke headless com budgets por fase
  (startup, switch por view, toggle+update, resize). Primeira layout CTk
  (~30–50 s neste ambiente) é pré-existente — budgets altos não são bug.

## 3. Qualidade

- Hook pre-commit: `ruff check src/core/ src/services/ ...` + `pytest tests/ -q`.
- Lógica nova pede teste; `tests/test_icons.py` trava regressão de emoji
  em `src/ui` + `mensagens.py` — manter a lista de permissão mínima.
