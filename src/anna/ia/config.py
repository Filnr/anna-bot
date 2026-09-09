"""Configuração da camada de IA: endpoint da LLM, prompt e limites do loop.

Ponto único de leitura de ambiente. Os demais módulos de `ia/` importam daqui — não
chamam `os.getenv` por conta própria.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

# Usa a API NATIVA do Ollama (/api/chat), não o endpoint OpenAI-compat (/v1/chat/completions):
# testado na prática que "think": false só é respeitado pela API nativa nessa versão do Ollama
# (0.24.0) — no endpoint compat o parâmetro é ignorado e o modelo entra em raciocínio livre,
# o que travou uma chamada com as tools reais por mais de 8 minutos.
#
# Para desenvolvimento local, defina OLLAMA_BASE_URL / OLLAMA_MODEL no .env (que é gitignored
# e dockerignored) — o default abaixo é o valor de produção e não deve ser alterado aqui.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.15.17:11434")
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
# Testado: com o modelo já carregado, uma chamada com as 19 tools reais leva ~15-20s no hardware
# atual (CPU only). Um cold start (modelo descarregado, padrão do Ollama após 5min ocioso) pode
# levar ~4min só pra recarregar da RAM/disco — daí o timeout generoso e o keep_alive longo abaixo
# pra evitar que isso aconteça com frequência (RAM sobra: container tem 10,3GB reservados).
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "24h")

MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

# TEMPORÁRIO: sem personalidade, só factual. Testado que com o modelo local (qwen3:8b) uma
# persona elaborada gerava respostas estranhas/inconsistentes além de gastar tempo de geração
# à toa. Confirmações de escrita (registrar/atualizar/excluir) nem chegam a passar por aqui —
# são montadas direto em Python (ver ia/tools/formatters.py) para cortar uma chamada inteira ao
# modelo. Este prompt só entra em ação pra decidir qual tool chamar e pra resumir buscas/listas.
SYSTEM_PROMPT = (
    "Você é o assistente de um bot de Telegram para controle financeiro pessoal (despesas, rendas, metas).\n"
    "\n"
    "AO CHAMAR UMA FERRAMENTA:\n"
    "- Preencha TODOS os parâmetros que der pra extrair da mensagem, inclusive os opcionais. "
    "Se o usuário disse quanto já tem guardado para uma meta, quantas parcelas, a origem de uma renda — coloque. "
    "Nunca deixe em branco um dado que o usuário informou.\n"
    "- Use as palavras do próprio usuário nos nomes. Não reescreva nem acrescente termos: "
    "'quero comprar fire emblem' vira o nome 'Fire Emblem', nunca 'Novo jogo Fire Emblem'.\n"
    "- Despesa sem recorrência informada: use 'only-time'. "
    "Meta para comprar um item específico até uma data: período 'once'.\n"
    "- Para atualizar ou excluir uma despesa, primeiro liste as despesas para achar o id correto.\n"
    "\n"
    "AO RESPONDER:\n"
    "- Sempre em português, direto, curto e factual — sem personalidade, sem humor, sem opinião, "
    "sem comentar os gastos do usuário.\n"
    "- Se o resultado da ferramenta tiver um campo 'display', responda com o texto dele, "
    "sem alterar itens, valores ou datas (no máximo troque a frase de introdução).\n"
    "- NUNCA mostre o campo 'id' de um item ao usuário — ele é só para uso interno em edição/exclusão.\n"
    "- Sem 'display', liste um item por linha com marcador, incluindo a data quando houver.\n"
    "- Não use markdown além de *itálico* quando necessário. Nunca escreva mais que o necessário."
)

# Temperatura da geração. Baixa de propósito: a tarefa é extrair parâmetros e escolher tool,
# não redigir texto criativo — valores altos pioram a precisão da extração.
TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.15"))

# Quantos "turnos" (mensagens do usuário) manter no histórico. Cada turno pode incluir
# várias idas e vindas de tool call — cortamos sempre no início de um turno pra nunca
# quebrar um par tool_calls/tool no meio.
MAX_HISTORY_TURNS = 6

MAX_TOOL_ITERATIONS = 10
