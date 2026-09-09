"""Camada de IA do anna-bot: interpreta mensagens em linguagem natural via LLM com
function calling e executa as tools de despesas/rendas/metas.

Uso:
    from ia import chat, reset_chat
"""
from ia.agent import chat, reset_chat

__all__ = ["chat", "reset_chat"]
