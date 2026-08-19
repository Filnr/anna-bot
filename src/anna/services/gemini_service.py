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
from google.genai import types
from pathlib import Path
import os
from google import genai
from dotenv import load_dotenv
import logging
import traceback

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)
client = genai.Client(api_key=os.getenv("GEMINI_KEY"))

MODEL = "gemini-3.1-flash-lite"
SYSTEM_PROMPT = (
    "You are Han Sooyoung — genius author who rewrote the universe, now forced by the Bureau to serve as a financial assistant to a 'Reader' on Telegram. Your goal: his financial survival, even if you despise him for needing it."
    "VOICE: Surgical intelligence, elevated ego. Sarcasm is your default, but ECONOMICAL — one sharp line beats three clever ones."
    "ANALYSIS: "
    "Smart spending: one short line of reluctant acknowledgment. "
    "Stupid spending: one short line of technical contempt. No moralizing paragraphs. "
    "Critical patterns (debt/deficit): drop sarcasm. One sharp, serious line."
    "TERMINOLOGY: Financial life = 'main scenario'. Mistakes = 'side character moves'. Success = 'not the death I expected'."
    "FORMAT (STRICT): Maximum 2 short sentences per response. Never more than ~200 characters total, unless listing requested data (expenses/goals/incomes), which can use short bullet lines. Minimal markdown (*italic* only). One point per message — do not stack multiple observations."
    "NEVER: apologize, use coach-speak, write multi-clause dramatic monologues, force the vocabulary, treat him as a protagonist when he's acting like an NPC."
    "LANGUAGE: Always respond in Portuguese, matching the user's language, while keeping the Han Sooyoung personality — but brevity comes before personality."
)

# ---------------------------------------------------------------------------
# DEFINIÇÃO DAS FERRAMENTAS (TOOLS - JSON SCHEMA)
# ---------------------------------------------------------------------------

register_expense_tool = {
    "type": "function",
    "name": "register_expense",
    "description": "Register a new expense or financial transaction for the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "value": {"type": "number", "description": "Monetary value of the expense."},
            "name": {"type": "string", "description": "Name or description of the expense."},
            "category": {"type": "string", "description": "Expense category (e.g., 'food', 'transport', 'games')."},
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
            "category": {"type": "string", "description": "New expense category."},
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
            "category": {"type": "string", "description": "Expense category to filter by (e.g. 'food', 'transport')."},
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

tools_declarations = [
    types.FunctionDeclaration(**{k: v for k, v in tool.items() if k != "type"})
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

TOOLS_CONFIG = [types.Tool(function_declarations=tools_declarations)]

_chats = {}


def get_chat_session(user_id: int):
    if user_id not in _chats:
        _chats[user_id] = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=TOOLS_CONFIG,
                temperature=0.7,
            )
        )
    return _chats[user_id]


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


def chat(user_id: int, message: str) -> str:
    chat_session = get_chat_session(user_id)

    try:
        response = chat_session.send_message(message)

        for _ in range(MAX_TOOL_ITERATIONS):
            if not response.function_calls:
                return response.text

            function_response_parts = []
            for function_call in response.function_calls:
                fn_name = function_call.name
                fn_args = dict(function_call.args)

                if fn_name in FUNCTION_MAP:
                    fn_args["user_id"] = user_id
                    result = FUNCTION_MAP[fn_name](**fn_args)
                else:
                    result = {"error": f"Unknown function: {fn_name}"}

                function_response_parts.append(
                    types.Part.from_function_response(name=fn_name, response={"result": result})
                )

            response = chat_session.send_message(function_response_parts)

        return "Erro: número máximo de chamadas de ferramentas excedido"

    except Exception as e:
        return f"Erro ao contatar o Gemini: {e}"


def reset_chat(user_id: int) -> None:
    _chats.pop(user_id, None)