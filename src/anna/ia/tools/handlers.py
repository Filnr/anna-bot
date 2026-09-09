"""Implementação em Python de cada tool exposta à LLM.

Cada função abre sua própria `SessionLocal`, delega para o service de domínio e devolve
um dict serializável (`{"status": "success"|"error", ...}`). `FUNCTION_MAP` liga o nome
declarado no schema à função; `WRITE_FUNCTIONS` marca as ações terminais de escrita.
"""
import logging
import traceback

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
from ia.tools.categories import EXPENSE_CATEGORIES
from ia.tools.formatters import _fmt_date, _format_read_result

logger = logging.getLogger(__name__)


def _with_display(fn_name: str, result: dict) -> dict:
    """Anexa `display` (texto pronto em PT) a um resultado de consulta, quando aplicável."""
    text = _format_read_result(fn_name, result)
    if text:
        result["display"] = text
    return result


def register_expense(user_id: int, value: float, name: str, category: str, recurrence_type: str = "only-time", total_installment: int = 1) -> dict:
    db = SessionLocal()
    try:
        if category not in EXPENSE_CATEGORIES:
            category = "other"
        if recurrence_type not in ("monthly", "annual", "weekly", "only-time"):
            recurrence_type = "only-time"
        dto = ExpenseDTO(
            value=value,
            name=name,
            category=category,
            recurrence_type=recurrence_type,
            installment=1,
            total_installment=total_installment or 1,
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
        return _with_display("get_expenses_by_month", {
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
                    "date": _fmt_date(e.date),
                }
                for e in expenses
            ],
        })
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_last_month_expenses(user_id: int) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        expenses = service.select_by_last_month(user_id=user_id)
        return _with_display("get_last_month_expenses", {
            "status": "success",
            "count": len(expenses),
            "expenses": [
                {"id": e.id, "name": e.name, "value": e.value, "category": e.category, "date": _fmt_date(e.date)}
                for e in expenses
            ],
        })
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
        return {"status": "error", "message": f"Não há despesa com id {expense_id}. Chame get_expenses_by_month para listar e pegar o id correto antes de atualizar. (detalhe: {e})"}
    finally:
        db.close()


def delete_expense(user_id: int, expense_id: int) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        service.delete(user_id=user_id, expense_id=expense_id)
        return {"status": "success", "message": "Expense deleted successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Não há despesa com id {expense_id}. Chame get_expenses_by_month para listar e pegar o id correto antes de excluir. (detalhe: {e})"}
    finally:
        db.close()


def get_last_month_expenses_by_category(user_id: int, category: str) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        expenses = service.select_by_category_last_month(user_id=user_id, category=category)
        return _with_display("get_last_month_expenses_by_category", {
            "status": "success",
            "count": len(expenses),
            "expenses": [
                {"id": e.id, "name": e.name, "value": e.value, "category": e.category, "date": _fmt_date(e.date)}
                for e in expenses
            ],
        })
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_expenses_by_year(user_id: int, year: int) -> dict:
    db = SessionLocal()
    try:
        service = ExpensesService(ExpensesRepository(db))
        expenses = service.select_by_year(user_id=user_id, year=year)
        return _with_display("get_expenses_by_year", {
            "status": "success",
            "year": year,
            "count": len(expenses),
            "expenses": [
                {"id": e.id, "name": e.name, "value": e.value, "category": e.category, "date": _fmt_date(e.date)}
                for e in expenses
            ],
        })
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
        return _with_display("get_all_incomes", {
            "status": "success",
            "count": len(incomes),
            "incomes": [
                {"name": inc.name, "value": inc.value, "origin": inc.origin, "recurrence_type": inc.recurrence_type}
                for inc in incomes
            ],
        })
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
        return _with_display("get_income", {
            "status": "success",
            "income": {"name": income.name, "value": income.value, "origin": income.origin, "recurrence_type": income.recurrence_type},
        })
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_incomes_by_recurrence(user_id: int, recurrence_type: str) -> dict:
    db = SessionLocal()
    try:
        service = IncomeService(IncomeRepository(db))
        incomes = service.select_by_recurrence_type(user_id=user_id, income_recurrence=recurrence_type)
        return _with_display("get_incomes_by_recurrence", {
            "status": "success",
            "count": len(incomes),
            "incomes": [
                {"name": inc.name, "value": inc.value, "origin": inc.origin, "recurrence_type": inc.recurrence_type}
                for inc in incomes
            ],
        })
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
        return _with_display("get_all_goals", {
            "status": "success",
            "count": len(goals),
            "goals": [
                {"name": g.name, "type": g.type, "value": g.target_value, "accumulated_value": g.accumulated_value, "period": g.period}
                for g in goals
            ],
        })
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def get_goal(user_id: int, goal_name: str) -> dict:
    db = SessionLocal()
    try:
        service = GoalService(GoalRepository(db))
        goal = service.select_goal(user_id=user_id, goal_name=goal_name)
        return _with_display("get_goal", {
            "status": "success",
            "goal": {"name": goal.name, "type": goal.type, "value": goal.target_value, "accumulated_value": goal.accumulated_value, "period": goal.period},
        })
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

# Consultas: nunca alteram nada e trazem um campo `display` pronto quando bem-sucedidas.
READ_FUNCTIONS = {name for name in FUNCTION_MAP if name not in WRITE_FUNCTIONS}
