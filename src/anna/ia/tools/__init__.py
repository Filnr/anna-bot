"""Camada de ferramentas (function calling) da IA.

- `schemas`: declaração JSON Schema das tools -> `TOOLS_CONFIG` (enviado à LLM).
- `handlers`: implementação Python -> `FUNCTION_MAP`, `WRITE_FUNCTIONS`, `READ_FUNCTIONS`.
- `formatters`: texto pronto em PT — `display` das consultas e `_format_write_result`.
- `categories`: enum de categorias de despesa + rótulos PT.
"""
from ia.tools.schemas import TOOLS_CONFIG
from ia.tools.handlers import FUNCTION_MAP, WRITE_FUNCTIONS, READ_FUNCTIONS
from ia.tools.formatters import _format_write_result, _format_read_result
from ia.tools.categories import EXPENSE_CATEGORIES, CATEGORY_LABELS_PT

__all__ = [
    "TOOLS_CONFIG",
    "FUNCTION_MAP",
    "WRITE_FUNCTIONS",
    "READ_FUNCTIONS",
    "_format_write_result",
    "_format_read_result",
    "EXPENSE_CATEGORIES",
    "CATEGORY_LABELS_PT",
]
