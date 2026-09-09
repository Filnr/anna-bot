"""Camada de transporte com a LLM.

Ponto único de contato com o backend de inferência. Trocar de provedor (outro endpoint,
outra API) começa e termina aqui — o resto de `ia/` só conhece `call_llm(messages)`.
"""
import requests

from ia.config import MODEL, OLLAMA_CHAT_URL, OLLAMA_KEEP_ALIVE, OLLAMA_TIMEOUT, TEMPERATURE
from ia.tools import TOOLS_CONFIG


def call_llm(messages: list[dict]) -> dict:
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS_CONFIG,
        "think": False,
        "stream": False,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {"temperature": TEMPERATURE},
    }
    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=OLLAMA_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["message"]
