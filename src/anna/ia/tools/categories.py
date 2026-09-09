"""Categorias de despesa aceitas pelo sistema e seus rótulos em português.

Fonte da verdade para o `enum` de `category` nos schemas das tools e para a formatação
das confirmações de escrita.
"""

EXPENSE_CATEGORIES = [
    "food",
    "games",
    "transport",
    "housing",
    "health",
    "education",
    "entertainment",
    "shopping",
    "bills",
    "subscriptions",
    "travel",
    "other",
]

CATEGORY_LABELS_PT = {
    "food": "alimentação",
    "games": "jogos",
    "transport": "transporte",
    "housing": "moradia",
    "health": "saúde",
    "education": "educação",
    "entertainment": "entretenimento",
    "shopping": "compras",
    "bills": "contas",
    "subscriptions": "assinaturas",
    "travel": "viagem",
    "other": "outros",
}
