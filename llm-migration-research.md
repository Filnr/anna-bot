# Pesquisa: substituição do Gemini API

Status: pesquisa concluída, implementação pendente.

## Problema real

Não é o preço por token (gemini-3.1-flash-lite já é o tier mais barato do Gemini). O problema é a
**política de pré-pagamento**: agora exige depósito mínimo de R$60, mesmo pra um uso real de ~R$1/mês.
Não faz sentido pagar adiantado 60 meses de uso.

Custo por chamada também é inflado pela própria arquitetura atual (`gemini_service.py`): system prompt +
18 tool schemas em JSON (~2-3k tokens só de declaração de ferramentas) + histórico de chat que cresce a
cada mensagem via `client.chats.create`, sem cache nem truncamento. Isso é um multiplicador de custo que
existe em qualquer provedor escolhido, não é exclusividade do Gemini. Reduzir o tamanho do prompt/tools
enviado a cada chamada vale a pena independente da decisão abaixo.

Requisitos do usuário: uso pessoal praticamente mínimo, modelo não precisa ser inteligente nem rápido,
só não pode errar a categorização das despesas. Orçamento-alvo: até R$5/mês.

## Opção escolhida para aprofundar: self-host no notebook-servidor

Hardware disponível: notebook Samsung X30 (possivelmente Samsung Book X30, i5-10210U, 4C/8T) usado como
servidor, 24GB RAM, gráficos integrados (sem GPU dedicada).

Isso resolve o problema na raiz: custo marginal ≈ R$0 (só eletricidade), sem depósito mínimo de espécie
nenhuma.

### Viabilidade / estresse no hardware

- **Ocioso**: CPU/RAM ~0. Ollama descarrega o modelo da memória após 5 min sem uso por padrão
  (`OLLAMA_KEEP_ALIVE`, configurável). Só o processo do servidor Ollama fica residente (leve).
- **Em uso**: satura os núcleos da CPU (100%, várias threads) durante prefill + geração. Pra um modelo
  4-8B em Q4 nesse hardware, esperar bursts de ~10-40s por interação. Baixo volume diário = uso agregado
  de poucos minutos de CPU/dia, sem risco de dano por uso esporádico (diferente de carga sustentada).
- **Trade-off de `keep_alive`**: manter o modelo carregado mais tempo evita recarregar do disco a cada
  chamada isolada (custo de alguns segundos), em troca de manter ~3-6GB de RAM ocupados. Com 24GB
  disponíveis, dá pra deixar carregado o dia todo sem problema.
- CPU sem GPU dedicada = inferência 100% em CPU. Faixa esperada pra modelos 7-8B Q4: 4-15 tokens/s
  (geração), suficiente já que velocidade não é requisito.

### Sobre encurtar a resposta ("ok, registrado" em vez de manter a personalidade)

Ajuda pouco: o `SYSTEM_PROMPT` atual já limita a resposta a ~200 caracteres / 2 frases curtas, então a
geração de output já é pequena hoje. O maior custo é o **prefill** (prompt + 18 tools + histórico a cada
chamada), não o tamanho da resposta. Não é necessário abrir mão da personalidade só por causa de
performance — o ganho de cortar pra resposta fixa é marginal comparado a reduzir o prompt/histórico
enviado.

### Modelos candidatos (self-host, via Ollama)

| Modelo | RAM (Q4_K_M) | Notas |
|---|---|---|
| Qwen3-8B | ~4,6GB | Ponto de partida recomendado. Tool calling nativo, multilíngue (testar qualidade em PT-BR especificamente), Apache 2.0. |
| Qwen3-4B | ~2,5GB | Fallback se o 8B for lento demais na CPU. |
| Phi-4-mini (3,8B) | ~2,3GB | Mais leve de todos, ~12 tok/s em CPU comum, treinado com formato de function calling pela Microsoft. |
| Watt-Tool-8B / ToolACE-8B / Llama-3-Groq-8B-Tool-Use | ~4,6GB | Finetunes do Llama-3.1-8B especializados em acertar tool calls (topo do Berkeley Function Calling Leaderboard). Testar se Qwen3 falhar na categorização — risco de fluência PT-BR pior (tuning majoritariamente em inglês). |
| Qwen3-14B | maior | Considerar se precisão de categorização exigir mais que o 8B entrega; RAM sobra (24GB), só perde em velocidade. |

**Vantagem específica pra "não errar categorização"**: Ollama (desde v0.5) suporta *structured outputs*
com decodificação restrita por gramática (XGrammar). Definindo `category` como `enum` no JSON schema, o
modelo fica impossibilitado *sintaticamente* de gerar uma categoria fora da lista — garantia mais forte
que a maioria das APIs pagas oferece por padrão. Não garante que a categoria escolhida dentro do enum
seja a *certa* (isso ainda depende da qualidade do modelo), mas elimina categoria inventada/inválida.

Hoje o `category` no `register_expense_tool` (`gemini_service.py`) é `string` livre — trocar pra `enum`
com as categorias fixas do sistema é a maior alavanca de confiabilidade barata, independente de qual LLM
for escolhida.

### Contras do self-host

- Notebook precisa ficar ligado 24/7 (já é o caso hoje).
- Sem GPU, upgrade futuro pra modelo maior é limitado.
- Queda de luz/internet em casa = bot fora do ar (risco que já existe hoje).

## Opção alternativa (sem trocar arquitetura): API paga sem depósito mínimo

Se self-host não for prioridade imediata, resolve o incômodo do depósito sem grandes mudanças:

| Provedor/modelo | Input / Output (por 1M tokens) | Mínimo de depósito | Notas |
|---|---|---|---|
| **DeepSeek V3.2** | $0,14 / $0,28 | Nenhum — cobrança estritamente por uso, recarga flexível | Function calling com "strict mode" (valida JSON schema no servidor). Melhor opção se quiser resolver hoje sem mexer em infra. |
| Mistral Small 3.2/4 | $0,08-0,15 / $0,20-0,60 | Não confirmado, checar direto no console | Function calling + structured outputs nativos. |
| GPT-5-nano / GPT-4.1-nano (OpenAI) | $0,05 / $0,40 | US$5 (~R$26) mínimo de compra | Bem menor que os R$60 do Gemini, mas ainda existe mínimo. |

Groq (free tier: 30 req/min, até 14.400 req/dia) e Cloudflare Workers AI (10k "neurons"/dia grátis)
também suportam function calling e cobrem uso mínimo com folga, mas o ToS da Groq desaconselha
explicitamente uso "de produção" no tier grátis — baixo risco real dado o volume mínimo, mas vale ter
uma opção paga de backup (DeepSeek/Mistral) caso o free tier mude de política.

## Recomendação

Dado que o hardware já existe parado e velocidade não é requisito, self-hospedar resolve o problema na
raiz (R$0, sem depósito, controle total sobre a categorização via grammar). DeepSeek seria a rota
"resolve hoje, sem fricção de infra" caso prefira separar a migração em duas etapas: trocar de provedor
primeiro, avaliar self-host depois com calma.

## Próximos passos (quando for implementar)

1. Confirmar CPU exata do notebook (`lscpu`) pra calibrar expectativa de tokens/s.
2. Instalar Ollama, testar Qwen3-8B com os 18 tools atuais e um punhado de mensagens reais de despesas.
3. Trocar `category` de `string` livre pra `enum` no schema do `register_expense_tool` (e demais tools
   relevantes) — vale independente do provedor escolhido.
4. Comparar acerto de categorização entre Qwen3-8B, Qwen3-4B e os finetunes de tool-calling antes de
   fixar o modelo.
5. Reduzir tamanho do prompt/tools/histórico enviado a cada chamada (reaproveitar KV-cache do prefixo
   estático via Ollama/llama.cpp, truncar ou resumir histórico) — reduz custo/tempo de resposta
   independente da opção final.
6. Trocar o SDK `google-genai` pelo cliente compatível com OpenAI (Ollama expõe endpoint
   `/v1/chat/completions`) ou pela SDK oficial da DeepSeek, dependendo da opção escolhida.

## Fontes consultadas

- https://devtk.ai/en/models/gemini-3-1-flash-lite/
- https://teachaitools.blog/blog/cheapest-llm-apis-production-cost-comparison-2026
- https://www.silicondata.com/use-cases/openai-api-pricing-per-1m-tokens
- https://www.grizzlypeaksoftware.com/articles/p/groq-api-free-tier-limits-in-2026-what-you-actually-get-uwysd6mb
- https://console.groq.com/docs/legal/services-agreement
- https://pricepertoken.com/endpoints/cloudflare/free
- https://devtk.ai/en/blog/mistral-api-pricing-guide-2026/
- https://api-docs.deepseek.com/guides/function_calling
- https://tradingeconomics.com/brazil/currency
- https://localaimaster.com/blog/best-ollama-models-tool-calling
- https://www.popularai.org/p/best-cpu-only-local-llm-2026
- https://docs.ollama.com/capabilities/structured-outputs
- https://www.promptquorum.com/local-llms/best-cpu-only-llm
- https://deepseek.ai/pricing
- https://tokenmix.ai/blog/deepseek-topup-2026-balance-recharge-refund
- https://help.openai.com/en/articles/8264778-what-is-prepaid-billing
- https://markaicode.com/ollama-keep-alive-memory-management/
- https://docs.ollama.com/faq
- https://www.hardware-corner.net/guides/qwen3-hardware-requirements/
- https://kelaptop.com/en/samsung-book-x30-np550xcj-kf1br
