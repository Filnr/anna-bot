"""Compat shim. A implementação foi movida para o pacote `ia/` (ver src/anna/ia/).

Mantido só para não quebrar `import services.llm_service`. Código novo deve usar
`from ia import chat, reset_chat`.
"""
from ia import chat, reset_chat  # noqa: F401
