"""Definição das ferramentas (tools) expostas à LLM, em JSON Schema.

Cada tool é declarada num dict `*_tool` e no fim convertida para o formato de tools do
endpoint (`{"type": "function", "function": {...}}`) em `TOOLS_CONFIG`.
"""
from ia.tools.categories import EXPENSE_CATEGORIES

register_expense_tool = {
    "type": "function",
    "name": "register_expense",
    "description": "Register a new expense or financial transaction for the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "value": {"type": "number", "description": "Monetary value of the expense."},
            "name": {"type": "string", "description": "Name or description of the expense."},
            "category": {
                "type": "string",
                "enum": EXPENSE_CATEGORIES,
                "description": "Expense category. 'games' and 'food' are their own categories — do not fold them into 'entertainment'.",
            },
            "recurrence_type": {
                "type": "string",
                "enum": ["monthly", "annual", "weekly", "only-time"],
                "description": "Recurrence pattern. If the user does not mention recurrence, use 'only-time'.",
            },
            "total_installment": {
                "type": "integer",
                "description": "Total number of installments, if the user mentions splitting payment (e.g. '3x'). Default is 1.",
            },
        },
        "required": ["value", "name", "category"],
    },
}

get_expenses_by_month_tool = {
    "type": "function",
    "name": "get_expenses_by_month",
    "description": "Retrieve the user's registered expenses for a specific month (1-12).",
    "parameters": {
        "type": "object",
        "properties": {
            "month": {"type": "integer", "description": "Month number (1 for January, 12 for December)."}
        },
        "required": ["month"],
    },
}

get_last_month_expenses_tool = {
    "type": "function",
    "name": "get_last_month_expenses",
    "description": "Retrieve the user's registered expenses for the previous month.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

register_income_tool = {
    "type": "function",
    "name": "register_income",
    "description": "Register a new income source or payment received.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name or title of the income (e.g. 'Salary', 'Freelance')."},
            "value": {"type": "number", "description": "Monetary value received."},
            "origin": {"type": "string", "description": "Origin of the income (e.g. 'Company X', 'Bank')."},
            "recurrence_type": {
                "type": "string",
                "enum": ["monthly", "annual", "weekly"],
                "description": "Recurrence type of the income.",
            },
        },
        "required": ["name", "value", "origin", "recurrence_type"],
    },
}

get_all_incomes_tool = {
    "type": "function",
    "name": "get_all_incomes",
    "description": "List all registered income entries for the user.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

register_goal_tool = {
    "type": "function",
    "name": "register_goal",
    "description": "Create a new financial goal or savings objective.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Short goal name using the user's OWN words for the item/objective. Do not add words like 'novo'/'new' or 'jogo'/'game': 'quero comprar fire emblem' -> name 'Fire Emblem'."},
            "type": {
                "type": "string",
                "enum": ["e", "c"],
                "description": "'c' when the user wants to BUY a specific item (game, phone, car...). 'e' for a general savings fund with no specific purchase (e.g. emergency fund).",
            },
            "value": {"type": "number", "description": "Target monetary value / price of the goal."},
            "accumulated_value": {"type": "number", "description": "How much the user has ALREADY saved toward this goal right now. Fill it whenever the user states an amount they currently have (e.g. 'tenho 100 reais', 'já juntei 200'). Use 0 only if they say they have nothing."},
            "period": {
                "type": "string",
                "enum": ["weekly", "monthly", "quarterly", "yearly", "once"],
                "description": "How often the user will set money aside. Use 'once' when it's a one-off purchase to be made by a deadline (e.g. 'compro até outubro').",
            },
        },
        "required": ["name", "type", "value", "period"],
    },
}

get_all_goals_tool = {
    "type": "function",
    "name": "get_all_goals",
    "description": "Retrieve all registered financial goals for the user.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

get_goal_tool = {
    "type": "function",
    "name": "get_goal",
    "description": "Retrieve a single financial goal by its exact name.",
    "parameters": {
        "type": "object",
        "properties": {
            "goal_name": {"type": "string", "description": "Exact name of the goal."},
        },
        "required": ["goal_name"],
    },
}

update_goal_tool = {
    "type": "function",
    "name": "update_goal",
    "description": "Update an existing financial goal, identified by its current name. All fields must be provided with their new (or unchanged) values.",
    "parameters": {
        "type": "object",
        "properties": {
            "goal_name": {"type": "string", "description": "Current name of the goal to update."},
            "new_name": {"type": "string", "description": "New name for the goal (same as goal_name if not renaming)."},
            "type": {
                "type": "string",
                "enum": ["e", "c"],
                "description": "'c' to buy a specific item, 'e' for a general savings fund with no specific purchase.",
            },
            "value": {"type": "number", "description": "New target monetary value / price for the goal."},
            "accumulated_value": {"type": "number", "description": "Total amount saved so far. Keep the current value if the user is not changing it."},
            "period": {
                "type": "string",
                "enum": ["weekly", "monthly", "quarterly", "yearly", "once"],
                "description": "How often the user sets money aside, or 'once' for a one-off purchase by a deadline.",
            },
        },
        "required": ["goal_name", "new_name", "type", "value", "accumulated_value", "period"],
    },
}

delete_goal_tool = {
    "type": "function",
    "name": "delete_goal",
    "description": "Delete a financial goal by its exact name.",
    "parameters": {
        "type": "object",
        "properties": {
            "goal_name": {"type": "string", "description": "Exact name of the goal to delete."},
        },
        "required": ["goal_name"],
    },
}

contribute_to_goal_tool = {
    "type": "function",
    "name": "contribute_to_goal",
    "description": "Add money to a goal's accumulated (saved) value, e.g. when the user says they saved/deposited towards a goal.",
    "parameters": {
        "type": "object",
        "properties": {
            "goal_name": {"type": "string", "description": "Exact name of the goal."},
            "amount": {"type": "number", "description": "Amount of money to add to the goal's accumulated value."},
        },
        "required": ["goal_name", "amount"],
    },
}

update_expense_tool = {
    "type": "function",
    "name": "update_expense",
    "description": "Update an existing expense, identified by its id. Use get_expenses_by_month or get_last_month_expenses first to find the correct expense_id.",
    "parameters": {
        "type": "object",
        "properties": {
            "expense_id": {"type": "integer", "description": "Id of the expense to update."},
            "value": {"type": "number", "description": "New monetary value of the expense."},
            "name": {"type": "string", "description": "New name or description of the expense."},
            "category": {
                "type": "string",
                "enum": EXPENSE_CATEGORIES,
                "description": "New expense category. 'games' and 'food' are their own categories — do not fold them into 'entertainment'.",
            },
            "recurrence_type": {
                "type": "string",
                "enum": ["monthly", "annual", "weekly", "only-time"],
                "description": "New recurrence pattern of the expense.",
            },
        },
        "required": ["expense_id", "value", "name", "category", "recurrence_type"],
    },
}

delete_expense_tool = {
    "type": "function",
    "name": "delete_expense",
    "description": "Delete an expense by its id. Use get_expenses_by_month or get_last_month_expenses first to find the correct expense_id.",
    "parameters": {
        "type": "object",
        "properties": {
            "expense_id": {"type": "integer", "description": "Id of the expense to delete."},
        },
        "required": ["expense_id"],
    },
}

get_expenses_by_category_tool = {
    "type": "function",
    "name": "get_last_month_expenses_by_category",
    "description": "Retrieve the user's expenses from the previous month, filtered by category.",
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": EXPENSE_CATEGORIES,
                "description": "Expense category to filter by.",
            },
        },
        "required": ["category"],
    },
}

get_expenses_by_year_tool = {
    "type": "function",
    "name": "get_expenses_by_year",
    "description": "Retrieve all of the user's registered expenses for a specific year.",
    "parameters": {
        "type": "object",
        "properties": {
            "year": {"type": "integer", "description": "Year to retrieve expenses for (e.g. 2026)."},
        },
        "required": ["year"],
    },
}

update_income_tool = {
    "type": "function",
    "name": "update_income",
    "description": "Update an existing income, identified by its current name. All fields must be provided with their new (or unchanged) values.",
    "parameters": {
        "type": "object",
        "properties": {
            "income_name": {"type": "string", "description": "Current name of the income to update."},
            "new_name": {"type": "string", "description": "New name for the income (same as income_name if not renaming)."},
            "value": {"type": "number", "description": "New monetary value received."},
            "origin": {"type": "string", "description": "New origin of the income."},
            "recurrence_type": {
                "type": "string",
                "enum": ["monthly", "annual", "weekly"],
                "description": "New recurrence type of the income.",
            },
        },
        "required": ["income_name", "new_name", "value", "origin", "recurrence_type"],
    },
}

delete_income_tool = {
    "type": "function",
    "name": "delete_income",
    "description": "Delete an income by its exact name.",
    "parameters": {
        "type": "object",
        "properties": {
            "income_name": {"type": "string", "description": "Exact name of the income to delete."},
        },
        "required": ["income_name"],
    },
}

get_income_tool = {
    "type": "function",
    "name": "get_income",
    "description": "Retrieve a single income entry by its exact name.",
    "parameters": {
        "type": "object",
        "properties": {
            "income_name": {"type": "string", "description": "Exact name of the income."},
        },
        "required": ["income_name"],
    },
}

get_incomes_by_recurrence_tool = {
    "type": "function",
    "name": "get_incomes_by_recurrence",
    "description": "Retrieve all incomes matching a given recurrence type (e.g. all monthly incomes).",
    "parameters": {
        "type": "object",
        "properties": {
            "recurrence_type": {
                "type": "string",
                "enum": ["monthly", "annual", "weekly"],
                "description": "Recurrence type to filter by.",
            },
        },
        "required": ["recurrence_type"],
    },
}


def _to_openai_tool(tool: dict) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }


TOOLS_CONFIG = [
    _to_openai_tool(tool)
    for tool in [
        register_expense_tool,
        get_expenses_by_month_tool,
        get_last_month_expenses_tool,
        update_expense_tool,
        delete_expense_tool,
        get_expenses_by_category_tool,
        get_expenses_by_year_tool,
        register_income_tool,
        get_all_incomes_tool,
        update_income_tool,
        delete_income_tool,
        get_income_tool,
        get_incomes_by_recurrence_tool,
        register_goal_tool,
        get_all_goals_tool,
        get_goal_tool,
        update_goal_tool,
        delete_goal_tool,
        contribute_to_goal_tool,
    ]
]
