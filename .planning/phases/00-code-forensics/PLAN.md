# PLAN — Fase 00 · Forense & Correções de Risco

> **Paleta de tema** · `preto #020617` · `verde #10B981` · `verde escuro #059669` · `superfície #0B1220` · `borda #1E293B`
> **Tema:** moderno minimalista, preto e verde.
> **Relatório de origem:** `forensics/report-20260922-102921.md`
> **Status:** ⬜ planejada

---

## Objetivo da fase

Reduzir os riscos da varredura forense: eliminar crashes intermitentes de UI, fechar a causa raiz de dependências silenciosas, corrigir dessincronização de estado (`lote_fontes`, KPIs, import/backup) e alinhar padrões de escrita. **Nenhuma mudança visual de produto** — apenas correções internas.

---

## Entregas (Waves)

### Wave 1 — Threading & Instalação (P0)

| # | Task | Esforço | Critério de aceite |
|---|------|---------|--------------------|
| 1.1 | Marshallizar `on_prog`/`on_err` via `self.after(0, ...)` em `gerar_view._extrair` | S | Sem chamada de widget fora da main thread (audit estático + teste de registro) |
| 1.2 | Aplicar o mesmo marshalling `on_prog` no fluxo de extração único | S | `prog`/`lbl` só atualizados via `after` |
| 1.3 | Instaladores: adicionar `lxml` explícito, remover `2>/dev/null || true`, verificar imports pós-instalação com mensagem de erro clara | M | `bash -n` passa; instalação com pip fail → abort com saída de erro |
| 1.4 | `requirements.txt`: consolidar `lxml>=4.9.0` (já feito) + snake check de versões | S | `pip check` sem conflito |

### Wave 2 — Estado & Consistência (P1)

| # | Task | Esforço | Critério de aceite |
|---|------|---------|--------------------|
| 2.1 | Refactor do refresh de KPIs em `modelo_view._refresh` — referência direta aos labels de valor, limpar `except:` e loop destrutivo | M | KPI "Modelos carregados" persiste e atualiza (teste de label via font_size estável) |
| 2.2 | `MapeamentoService._sync_lote`: remover `placeholder` de todas as entradas antes de gravar no novo doc | M | Teste: remapear ph de doc A→B deixa A sem o ph |
| 2.3 | `_update_canvas`: desenhar a partir de fonte única (mantém `mapeamento` como verdade; lote só para docs sem mapeamento global) | S | Sem retângulo duplicado após remap |
| 2.4 | OCR de lote em thread com progresso (reutilizar padrão de `extrair_todos` marshallizado) — `gerar_view._gerar` lote | M | UI responsiva; progresso visível; testes de unidade do serviço de lote |
| 2.5 | Escrita atômica em `historico.salvar_historico` e `preferencias.salvar_preferencias` (tmp + `os.replace`) | S | Crash simulado não corrompe arquivo; padrão igual a `modelos_salvos` |
| 2.6 | Remover dead statements `old['documento_path']` e `self.state.mapeamento[ph]['documento_path']` | S | `ruff` sem achados; diff limpo |

### Wave 3 — DOCX & Legado (P2)

| # | Task | Esforço | Critério de aceite |
|---|------|---------|--------------------|
| 3.1 | Tratar hyperlinks no DOCX: substituição/extração de placeholders em runs de hyperlink | M | Teste com doc contendo link com `{{campo}}` → substituído e extraído |
| 3.2 | Revisar `_replace_in_paragraph`: preservar formatação por segmento (ou documentar limitação + fallback) | M | Formatação bold/font de trechos mantida; testes de regressão |
| 3.3 | `importar`: validar existência de docs referenciados e avisar (mensagem) em vez de `pass` | S | Import com doc inexistente → aviso explícito, sem estado órfão silencioso |
| 3.4 | Decisão de lifecycle do legado: registrar ADR (deprecar `interface.py`/`interface_ctk.py` ou pipeline de sync) | S | ADR aceito; scripts de run ajustados se deprecar |

---

## Verificação

- `pytest` verde (suite + novos testes das tasks 2.2, 2.4, 3.1)
- `ruff` sem novas inconformidades (se disponível na CI)
- Smoke manual: carregar modelo, mapear em 2 docs, remapear um campo, gerar lote → sem freeze e sem duplicação de retângulos
- Background: instalação limpa simula pip falho → erro visível
- Tema preto/verde aplicado consistentemente nas telas ao alternar dark/light (sem branco puro no escuro)

---

## Fora de escopo desta fase

- Redesign de UI / novas features
- Migração do legado (apenas decisão + ADR)
- Perf de OCR

---

*Documento gerado por análise forense · tema preto `#020617` / verde `#10B981`.*