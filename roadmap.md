# Anna Bot — roadmap

Bot de controle financeiro pessoal via Telegram (substituto de planilha Excel). O usuário manda
mensagens em linguagem natural (ex: "gastei 50 reais comprando final fantasy") e o bot/LLM entende,
categoriza e registra a despesa/receita/meta automaticamente.

## Concluído

- Modelagem de dados: despesas (Expenses), receitas (Income), metas (Goals), usuário.
- CRUD completo de despesas via LLM com function calling: registrar (com parcelamento e recorrência),
  listar por mês/ano/categoria, atualizar, deletar.
- CRUD completo de receitas via LLM: registrar, listar, atualizar, deletar, filtrar por recorrência.
- CRUD completo de metas financeiras via LLM: criar, listar, atualizar, deletar, contribuir valor.
- Integração com LLM (Gemini) via function calling para interpretar mensagens em linguagem natural e
  chamar as ferramentas certas, com personalidade fixa no system prompt.
- Bot rodando no Telegram.

## Em andamento / próximo

- **Trocar o provedor de LLM.** Gemini passou a exigir depósito mínimo de R$60, inviável pro uso real
  (~R$1/mês). Ver pesquisa completa em `llm-migration-research.md` — opções: self-host (Qwen3-8B via
  Ollama no notebook-servidor) ou API sem depósito mínimo (DeepSeek). Ao trocar, também trocar `category`
  de string livre pra `enum` no schema das tools, pra reduzir erro de categorização.
- **Exportação de despesas em Excel.** Uma planilha (aba) por mês, cobrindo até 5 meses de histórico a
  depender do período solicitado pelo usuário.
- **Análise de despesas com ML.** Ex: identificar maior gasto do período, detectar aumento anômalo de
  gasto (fora do padrão histórico) em uma categoria, etc.

## Ideias futuras (quanto mais ferramentas de análise financeira, melhor)

- Outras análises automáticas: gasto médio por categoria, projeção de gasto do mês com base no histórico,
  alertas quando uma categoria estourar a média.
- Explorar mais ferramentas/relatórios de controle financeiro pessoal além do que já está listado acima —
  lista aberta, adicionar aqui conforme surgirem ideias.
