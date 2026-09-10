# Anna Bot

Bot de Telegram para controle financeiro pessoal. O usuário manda mensagens em linguagem
natural ("gastei 50 reais com o mercado", "quanto gastei em jogos mês passado?") e o bot
entende, categoriza e registra despesas, receitas e metas automaticamente via LLM com function
calling.

## Escopo do projeto

Este é um projeto pessoal, não um serviço público:

- Acesso é restrito ao autor e a pessoas específicas aprovadas manualmente (ver
  [Controle de acesso](#controle-de-acesso)) — não há cadastro aberto/self-service.
- O uso é espontâneo e não padronizado: não existe um volume de tráfego previsível, escalável ou
  agendado, é uma pessoa mandando mensagem quando lembra de registrar um gasto.
- Existe a possibilidade de, no futuro, evoluir isso para um SaaS multi-tenant (já há um modelo
  `Subscription` no banco, hoje não utilizado). Isso é só uma direção em aberto — **não** deve
  influenciar decisões de arquitetura agora. Simplificações como histórico de conversa em
  memória e aprovação de acesso manual são aceitáveis no escopo atual e serão revistas se/quando
  fizer sentido crescer.

## Como funciona

```
Telegram (python-telegram-bot)
        │
        ▼
  src/anna/bot/bot.py          — handlers, autenticação, loop de polling
        │
        ▼
  src/anna/ia/                 — orquestração da LLM (function calling)
    config.py                  — env, system prompt, limites do loop
    client.py                  — transporte HTTP com o backend de inferência (Ollama)
    agent.py                   — loop de tool-calling, histórico por usuário
    tools/                     — schemas das tools + implementação + formatação em PT-BR
        │
        ▼
  services/ + repositories/    — regras de domínio (despesas, receitas, metas, usuário)
        │
        ▼
  PostgreSQL (Supabase)
```

O backend de LLM é o Ollama (API nativa `/api/chat`), configurável via env — ver
`ia/client.py`/`ia/config.py` para detalhes e o histórico da migração (Gemini → Ollama) em
`llm-migration-research.md`.

## Funcionalidades

- Registro, consulta, atualização e exclusão de **despesas** (com parcelamento e recorrência).
- Registro, consulta, atualização e exclusão de **receitas**.
- Criação, consulta, atualização, exclusão e contribuição em **metas financeiras**.
- Tudo via linguagem natural, com a LLM decidindo qual ferramenta chamar e extraindo os
  parâmetros da mensagem.

Lista completa e itens em andamento: [`roadmap.md`](./roadmap.md).

## Requisitos

- Python >= 3.13 (ambiente de desenvolvimento atual usa 3.14)
- [Poetry](https://python-poetry.org/)
- Um banco PostgreSQL acessível (hoje: Supabase)
- Um servidor Ollama acessível pela rede, com o modelo desejado já baixado

## Configuração

Copie `.env.example` para `.env` e preencha:

| Variável | Obrigatória | Descrição |
|---|---|---|
| `BOT_TOKEN` | sim | Token do bot no Telegram (BotFather). |
| `BOT_NAME` | sim | Handle do bot (`@SeuBot`) — usado para detectar menções em grupos. |
| `ADMIN` | sim | Telegram ID do admin. |
| `USER_TEST` | não | ID auxiliar para testes manuais. |
| `DATABASE_URL` | sim | Connection string do Postgres (`postgresql://user:pass@host:5432/db`). |
| `SUPABASE_PASSWORD` | não | Só se estiver usando Supabase e precisar dela separadamente. |
| `OLLAMA_BASE_URL` | não | Endpoint do Ollama. Default de produção em `ia/config.py`. |
| `OLLAMA_MODEL` | não | Modelo a usar (default: `qwen3:8b`). |
| `OLLAMA_TIMEOUT` | não | Timeout da chamada em segundos (default: `300`). |
| `OLLAMA_KEEP_ALIVE` | não | Tempo que o Ollama mantém o modelo carregado (default: `24h`). |
| `OLLAMA_TEMPERATURE` | não | Temperatura de geração (default: `0.15` — baixa de propósito). |
| `GEMINI_KEY` | — | **Legado, não usado.** Sobra da integração antiga com Gemini. |

## Rodando localmente

```bash
poetry install
cp .env.example .env   # preencher com valores reais
PYTHONPATH=src/anna poetry run python src/anna/bot/bot.py
```

O `PYTHONPATH=src/anna` é necessário porque o código importa módulos como `services.xxx`
(sem prefixo `anna.`), assumindo `src/anna` no `sys.path` — isso só acontece "de graça" dentro
de uma IDE que marca `src/anna` como source root (ex. PyCharm). Rodando puro pelo terminal ou
via Docker, a env var precisa ser setada explicitamente (o `Dockerfile` já faz isso).

## Rodando em produção (Docker / ZimaOS)

O `.github/workflows/deploy.yml` builda e publica a imagem em
`ghcr.io/filnr/anna-bot:latest` a cada push em `main` — não é necessário buildar na própria NAS.

Na ZimaOS (ou qualquer host com Docker):

```bash
cp .env.example .env   # preencher com valores de produção
docker compose up -d
```

O `docker-compose.yml` já usa `restart: unless-stopped`, então o bot volta sozinho após reboot
ou crash do container. `OLLAMA_BASE_URL` deve apontar para o IP/porta do Ollama na rede local —
o container alcança a LAN normalmente sem configuração extra de rede.

## Controle de acesso

`/register` **apenas cria o cadastro** — não concede acesso ao bot. Todo usuário novo entra com
`free_access = false`. Para liberar alguém, o admin roda manualmente no banco (Supabase):

```sql
UPDATE "user" SET free_access = true WHERE telegram_id = <telegram_id_da_pessoa>;
```

Isso é intencionalmente manual: o volume de aprovações é baixo (uso pessoal, poucas pessoas
específicas), então não há comando dedicado no bot para isso ainda.

## Testes

```bash
PYTHONPATH=src/anna poetry run pytest
```

(mesmo motivo do `PYTHONPATH` em [Rodando localmente](#rodando-localmente) — `tests/conftest.py`
importa `core.database` sem prefixo `anna.`.)

## Limitações conhecidas

- **Histórico de conversa em memória** (`ia/agent.py`): não sobrevive a um restart do processo e
  cresce sem limite de usuários distintos ao longo do tempo. Aceitável no volume atual.
- **Aprovação de acesso manual** via `UPDATE` direto no banco — sem comando `/aprovar` ou painel.
- **Um único backend/modelo de LLM fixo por variável de ambiente** — sem troca por usuário ou
  fallback automático entre provedores.

## Roadmap

Itens concluídos, em andamento e ideias futuras: [`roadmap.md`](./roadmap.md). Vale destacar que
uma eventual virada para SaaS (multi-tenant, cobrança via o modelo `Subscription` já modelado no
banco, autenticação mais robusta) é uma direção possível, não um compromisso atual.
