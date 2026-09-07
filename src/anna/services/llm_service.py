from services.expense_service import ExpensesService
from services.income_service import IncomeService
from services.goal_service import GoalService
from repositories.expense_repository import ExpensesRepository
from repositories.income_repository import IncomeRepository
from repositories.goal_repository import GoalRepository
from schemas.expenses import ExpenseDTO
from schemas.income import IncomeDTO
from schemas.goal import GoalDTO
from core.database import SessionLocal
from pathlib import Path
import os
import json
import requests
from dotenv import load_dotenv
import logging
import traceback

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

# TEMPORÁRIO: aponta direto pro Ollama rodando no notebook-servidor (ZimaOS) via Tailscale/rede local.
# Quando existir camada intermediária para acesso fora de casa, isso deixa de ser fixo.
#
# Usa a API NATIVA do Ollama (/api/chat), não o endpoint OpenAI-compat (/v1/chat/completions):
# testado na prática que "think": false só é respeitado pela API nativa nessa versão do Ollama
# (0.24.0) — no endpoint compat o parâmetro é ignorado e o modelo entra em raciocínio livre,
# o que travou uma chamada com as tools reais por mais de 8 minutos.
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
# são montadas 2direto em Python (ver _format_write_result) para cortar uma chamada inteira ao
# modelo. Este prompt só entra em ação pra decidir qual tool chamar e pra resumir buscas/listas.
SYSTEM_PROMPT = (
    "Você é o assistente de um bot de Telegram para controle financeiro pessoal (despesas, rendas, metas). "
    "Responda sempre em português, de forma direta, curta e estritamente factual — sem personalidade, sem humor, sem opiniões, sem comentários sobre os gastos do usuário. "
    "Ao listar dados (despesas, rendas, metas), use linhas curtas com marcadores, uma por item. "
    "Não use markdown além de *itálico* quando necessário. Nunca escreva mais do que o necessário para responder."
)

# ---------------------------------------------------------------------------
# DEFINIÇÃO DAS FERRAMENTAS (TOOLS - JSON SCHEMA)
# ---------------------------------------------------------------------------

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
                "description": "Recurrence pattern of the expense.",
            },
            "total_installment": {
                "type": "integer",
                "description": "Total number of installments, if the user mentions splitting payment (e.g. '3x'). Default is 1.",
            },
        },
        "required": ["value", "name", "category", "recurrence_type"],
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
            "name": {"type": "string", "description": "Name of the financial goal (e.g. 'Novo celular', 'Reserva de emergência')."},
            "type": {
                "type": "string",
                "enum": ["e", "c"],
                "description": "'e' for a savings goal with no fixed purchase (e.g. emergency fund), 'c' for a goal to buy a specific item.",
            },
            "value": {"type": "number", "description": "Target monetary value for the goal."},
            "accumulated_value": {"type": "number", "description": "Amount already saved so far, if mentioned. Default is 0."},
            "period": {
                "type": "string",
                "enum": ["weekly", "monthly", "quarterly", "yearly", "once"],
                "description": "Timeframe/periodicity to reach the goal.",
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
                "description": "'e' for a savings goal with no fixed purchase, 'c' for a goal to buy a specific item.",
            },
            "value": {"type": "number", "description": "New target monetary value for the goal."},
            "accumulated_value": {"type": "number", "description": "New amount already saved."},
            "period": {
                "type": "string",
                "enum": ["weekly", "monthly", "quarterly", "yearly", "once"],
                "description": "Timeframe/periodicity to reach the goal.",
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

# Histórico manual por usuário (sem system prompt, que é sempre prependado na chamada).
_histories: dict[int, list[dict]] = {}

# Quantos "turnos" (mensagens do usuário) manter no histórico. Cada turno pode incluir
# várias idas e vindas de tool call — cortamos sempre no início de um turno pra nunca
# quebrar um par tool_calls/tool no meio.
MAX_HISTORY_TURNS = 6


def _trim_history(history: list[dict]) -> list[dict]:
    user_indices = [i for i, m in enumerate(history) if m["role"] == "user"]
    if len(user_indices) > MAX_HISTORY_TURNS:
        cutoff = user_indices[-MAX_HISTORY_TURNS]
        return history[cutoff:]
    return history


# ---------------------------------------------------------------------------
# IMPLEMENTAÇÃO DAS FUNÇÕES
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

def register_expense(user_id: int, value: float, name: str, category: str, recurrence_type: str, total_installment: int = 1) -> dict:
    db = SessionLocal()
    try:
        dto = ExpenseDTO(
            value=value,
            name=name,
            category=category,
            recurrence_type=recurrence_type,
            installment=1,
            total_installment=total_installment,
        )
        service = ExpensesService(ExpensesRepository(db))
        created_expenses = service.create(user_id=user_id, data=dto)
        return {
            "status": "success",
            "message": f"{len(created_expenses)} expense installment(s) registered successfully.",
            "total_value": value,
            "name": name,
        }
    except Exception as e:
        logger.error(f"Error in register_expense: {e}\n{traceback.format_exc()}")  # ✅ aparece no seu terminal
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_expenses_by_month(user_id: int, month: int) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        expenses = service.select_by_month(user_id=user_id, month=month)
        return {
            "status": "success",
            "month": month,
            "count": len(expenses),
            "expenses": [
                {
                    "id": e.id,
                    "name": e.name,
                    "value": e.value,
                    "category": e.category,
                    "installment": f"{e.installment}/{e.total_installment}",
                    "date": str(e.date),
                }
                for e in expenses
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_last_month_expenses(user_id: int) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        expenses = service.select_by_last_month(user_id=user_id)
        return {
            "status": "success",
            "count": len(expenses),
            "expenses": [
                {"id": e.id, "name": e.name, "value": e.value, "category": e.category, "date": str(e.date)}
                for e in expenses
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def update_expense(user_id: int, expense_id: int, value: float, name: str, category: str, recurrence_type: str) -> dict:
    db = SessionLocal()
    try:
        dto = ExpenseDTO(
            value=value,
            name=name,
            category=category,
            recurrence_type=recurrence_type,
            installment=1,
            total_installment=1,
        )
        service = ExpensesService(ExpensesRepository(db))
        expense = service.update(user_id=user_id, expense_id=expense_id, data=dto)
        return {"status": "success", "message": f"Expense '{expense.name}' updated successfully.", "value": expense.value}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def delete_expense(user_id: int, expense_id: int) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        service.delete(user_id=user_id, expense_id=expense_id)
        return {"status": "success", "message": "Expense deleted successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_last_month_expenses_by_category(user_id: int, category: str) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        expenses = service.select_by_category_last_month(user_id=user_id, category=category)
        return {
            "status": "success",
            "count": len(expenses),
            "expenses": [
                {"id": e.id, "name": e.name, "value": e.value, "category": e.category, "date": str(e.date)}
                for e in expenses
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_expenses_by_year(user_id: int, year: int) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        expenses = service.select_by_year(user_id=user_id, year=year)
        return {
            "status": "success",
            "year": year,
            "count": len(expenses),
            "expenses": [
                {"id": e.id, "name": e.name, "value": e.value, "category": e.category, "date": str(e.date)}
                for e in expenses
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def register_income(user_id: int, name: str, value: float, origin: str, recurrence_type: str) -> dict:
    db = SessionLocal()
    try:
        dto = IncomeDTO(name=name, value=value, origin=origin, recurrence_type=recurrence_type)
        service = IncomeService(IncomeRepository(db))
        income = service.create(user_id=user_id, data=dto)
        return {"status": "success", "message": f"Income '{income.name}' registered successfully.", "value": income.value}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_all_incomes(user_id: int) -> dict:
    db = SessionLocal()
    try:
        service = IncomeService(IncomeRepository(db))
        incomes = service.select_all(user_id=user_id)
        return {
            "status": "success",
            "count": len(incomes),
            "incomes": [
                {"name": inc.name, "value": inc.value, "origin": inc.origin, "recurrence_type": inc.recurrence_type}
                for inc in incomes
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def update_income(user_id: int, income_name: str, new_name: str, value: float, origin: str, recurrence_type: str) -> dict:
    db = SessionLocal()
    try:
        dto = IncomeDTO(name=new_name, value=value, origin=origin, recurrence_type=recurrence_type)
        service = IncomeService(IncomeRepository(db))
        income = service.update(user_id=user_id, income_name=income_name, data=dto)
        return {"status": "success", "message": f"Income '{income.name}' updated successfully.", "value": income.value}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def delete_income(user_id: int, income_name: str) -> dict:
    db = SessionLocal()
    try:
        service = IncomeService(IncomeRepository(db))
        service.delete(user_id=user_id, income_name=income_name)
        return {"status": "success", "message": "Income deleted successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_income(user_id: int, income_name: str) -> dict:
    db = SessionLocal()
    try:
        service = IncomeService(IncomeRepository(db))
        income = service.select_by_name(user_id=user_id, income_name=income_name)
        return {
            "status": "success",
            "income": {"name": income.name, "value": income.value, "origin": income.origin, "recurrence_type": income.recurrence_type},
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_incomes_by_recurrence(user_id: int, recurrence_type: str) -> dict:
    db = SessionLocal()
    try:
        service = IncomeService(IncomeRepository(db))
        incomes = service.select_by_recurrence_type(user_id=user_id, income_recurrence=recurrence_type)
        return {
            "status": "success",
            "count": len(incomes),
            "incomes": [
                {"name": inc.name, "value": inc.value, "origin": inc.origin, "recurrence_type": inc.recurrence_type}
                for inc in incomes
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def register_goal(
    user_id: int,
    name: str,
    type: str,
    value: float,
    period: str,
    accumulated_value: float = 0.0,
) -> dict:
    db = SessionLocal()
    try:
        dto = GoalDTO(name=name, type=type, value=value, accumulated_value=accumulated_value, period=period)
        service = GoalService(GoalRepository(db))
        goal = service.create(userid=user_id, data=dto)
        return {"status": "success", "message": f"Goal '{goal.name}' registered successfully.", "target_value": goal.target_value}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_all_goals(user_id: int) -> dict:
    db = SessionLocal()
    try:
        service = GoalService(GoalRepository(db))
        goals = service.select_all(userId=user_id)
        return {
            "status": "success",
            "count": len(goals),
            "goals": [
                {"name": g.name, "type": g.type, "value": g.target_value, "accumulated_value": g.accumulated_value, "period": g.period}
                for g in goals
            ],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_goal(user_id: int, goal_name: str) -> dict:
    db = SessionLocal()
    try:
        service = GoalService(GoalRepository(db))
        goal = service.select_goal(user_id=user_id, goal_name=goal_name)
        return {
            "status": "success",
            "goal": {"name": goal.name, "type": goal.type, "value": goal.target_value, "accumulated_value": goal.accumulated_value, "period": goal.period},
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def update_goal(
    user_id: int,
    goal_name: str,
    new_name: str,
    type: str,
    value: float,
    accumulated_value: float,
    period: str,
) -> dict:
    db = SessionLocal()
    try:
        dto = GoalDTO(name=new_name, type=type, value=value, accumulated_value=accumulated_value, period=period)
        service = GoalService(GoalRepository(db))
        goal = service.update(user_id=user_id, old_name_goal=goal_name, data=dto)
        return {"status": "success", "message": f"Goal '{goal.name}' updated successfully.", "target_value": goal.target_value}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def delete_goal(user_id: int, goal_name: str) -> dict:
    db = SessionLocal()
    try:
        service = GoalService(GoalRepository(db))
        service.delete(userId=user_id, goal_name=goal_name)
        return {"status": "success", "message": "Goal deleted successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def contribute_to_goal(user_id: int, goal_name: str, amount: float) -> dict:
    db = SessionLocal()
    try:
        service = GoalService(GoalRepository(db))
        goal = service.contribute(user_id=user_id, goal_name=goal_name, amount=amount)
        return {
            "status": "success",
            "message": f"Added {amount} to goal '{goal.name}'.",
            "accumulated_value": goal.accumulated_value,
            "target_value": goal.target_value,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


FUNCTION_MAP = {
    "register_expense": register_expense,
    "get_expenses_by_month": get_expenses_by_month,
    "get_last_month_expenses": get_last_month_expenses,
    "update_expense": update_expense,
    "delete_expense": delete_expense,
    "get_last_month_expenses_by_category": get_last_month_expenses_by_category,
    "get_expenses_by_year": get_expenses_by_year,
    "register_income": register_income,
    "get_all_incomes": get_all_incomes,
    "update_income": update_income,
    "delete_income": delete_income,
    "get_income": get_income,
    "get_incomes_by_recurrence": get_incomes_by_recurrence,
    "register_goal": register_goal,
    "get_all_goals": get_all_goals,
    "get_goal": get_goal,
    "update_goal": update_goal,
    "delete_goal": delete_goal,
    "contribute_to_goal": contribute_to_goal,
}

MAX_TOOL_ITERATIONS = 10


def _call_ollama(messages: list[dict]) -> dict:
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS_CONFIG,
        "think": False,
        "stream": False,
        "keep_alive": OLLAMA_KEEP_ALIVE,
        "options": {"temperature": 0.7},
    }
    resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=OLLAMA_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["message"]


# Ações de escrita (registrar/atualizar/excluir) são sempre terminais: uma vez executadas,
# não faz sentido o modelo decidir chamar outra tool. Respondemos direto em Python — sem essa
# segunda chamada, a resposta comum de "registrei sua despesa" fica bem mais rápida e não
# fica sujeita ao modelo inventar/distorcer o texto.
WRITE_FUNCTIONS = {
    "register_expense",
    "update_expense",
    "delete_expense",
    "register_income",
    "update_income",
    "delete_income",
    "register_goal",
    "update_goal",
    "delete_goal",
    "contribute_to_goal",
}


def _format_write_result(fn_name: str, fn_args: dict, result: dict) -> str:
    if result.get("status") != "success":
        return f"Erro: {result.get('message', 'falha desconhecida')}"

    if fn_name == "register_expense":
        label = CATEGORY_LABELS_PT.get(fn_args.get("category"), fn_args.get("category"))
        return f"Despesa registrada: {fn_args.get('name')} ({label}) — R$ {fn_args.get('value'):.2f}"
    if fn_name == "update_expense":
        label = CATEGORY_LABELS_PT.get(fn_args.get("category"), fn_args.get("category"))
        return f"Despesa atualizada: {fn_args.get('name')} ({label}) — R$ {fn_args.get('value'):.2f}"
    if fn_name == "delete_expense":
        return "Despesa removida com sucesso."

    if fn_name == "register_income":
        return f"Renda registrada: {fn_args.get('name')} — R$ {fn_args.get('value'):.2f}"
    if fn_name == "update_income":
        return f"Renda atualizada: {fn_args.get('new_name')} — R$ {fn_args.get('value'):.2f}"
    if fn_name == "delete_income":
        return f"Renda removida: {fn_args.get('income_name')}."

    if fn_name == "register_goal":
        return f"Meta registrada: {fn_args.get('name')} — R$ {fn_args.get('value'):.2f}"
    if fn_name == "update_goal":
        return f"Meta atualizada: {fn_args.get('new_name')} — R$ {fn_args.get('value'):.2f}"
    if fn_name == "delete_goal":
        return f"Meta removida: {fn_args.get('goal_name')}."
    if fn_name == "contribute_to_goal":
        accumulated = result.get("accumulated_value")
        target = result.get("target_value")
        return f"Contribuição registrada em '{fn_args.get('goal_name')}': +R$ {fn_args.get('amount'):.2f} (R$ {accumulated:.2f}/R$ {target:.2f})"

    return result.get("message", "Ação concluída com sucesso.")


def chat(user_id: int, message: str) -> str:
    history = _histories.setdefault(user_id, [])
    history.append({"role": "user", "content": message})

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
            assistant_message = _call_ollama(messages)
            tool_calls = assistant_message.get("tool_calls") or []

            if not tool_calls:
                content = assistant_message.get("content") or ""
                history.append({"role": "assistant", "content": content})
                _histories[user_id] = _trim_history(history)
                return content

            history.append({
                "role": "assistant",
                "content": assistant_message.get("content") or "",
                "tool_calls": tool_calls,
            })

            calls_this_round = []
            for i, tool_call in enumerate(tool_calls):
                fn = tool_call["function"]
                fn_name = fn["name"]
                fn_args = fn.get("arguments") or {}
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args or "{}")
                    except json.JSONDecodeError:
                        fn_args = {}

                if fn_name in FUNCTION_MAP:
                    result = FUNCTION_MAP[fn_name](user_id=user_id, **fn_args)
                else:
                    result = {"error": f"Unknown function: {fn_name}"}

                calls_this_round.append((fn_name, fn_args, result))
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", f"call_{i}"),
                    "content": json.dumps(result, ensure_ascii=False),
                })

            # Rodada só com ações de escrita: responde na hora, sem gastar outra chamada ao
            # modelo pra "narrar" o que já sabemos que aconteceu.
            if all(fn_name in WRITE_FUNCTIONS for fn_name, _, _ in calls_this_round):
                try:
                    lines = [_format_write_result(fn_name, fn_args, result) for fn_name, fn_args, result in calls_this_round]
                except Exception:
                    lines = [result.get("message", "Ação concluída.") for _, _, result in calls_this_round]
                reply = "\n".join(lines)
                history.append({"role": "assistant", "content": reply})
                _histories[user_id] = _trim_history(history)
                return reply

        _histories[user_id] = _trim_history(history)
        return "Erro: número máximo de chamadas de ferramentas excedido"

    except Exception as e:
        logger.error(f"Error in chat: {e}\n{traceback.format_exc()}")
        return f"Erro ao contatar a LLM: {e}"


def reset_chat(user_id: int) -> None:
    _histories.pop(user_id, None)
