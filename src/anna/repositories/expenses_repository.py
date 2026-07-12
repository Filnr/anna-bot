import datetime
from sqlalchemy import select, extract
from models.expenses import Expenses
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta


class ExpensesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, expense: Expenses) -> None:
        self.session.add(expense)
        self.session.commit()
        self.session.refresh(expense)

    def select_by_month(self, user_id: int, month: int, year: int = None) -> list[Expenses]:
        if year is None:
            year = datetime.datetime.now().year

        expenses = (
            self.session.query(Expenses)
            .filter(Expenses.user_id == user_id)
            .filter(extract('month', Expenses.date) == month)
            .filter(extract('year', Expenses.date) == year)
            .all()
        )
        return expenses

    def select_last_month_by_type(self, user_id: int, type: str) -> list[Expenses]:
        last_month = datetime.datetime.now() - relativedelta(months=1)
        expenses = (
            self.session.query(Expenses)
            .filter(Expenses.user_id == user_id)
            .filter(Expenses.type == type)
            .filter(Expenses.date >= last_month)
            .all()
        )
        return expenses

    def select_by_id(self, user_id: int, expense_id: int) -> list[Expenses]:
        expenses = (
            self.session.query(Expenses)
            .filter(Expenses.user_id == user_id)
            .filter(Expenses.id == expense_id)
            .all()
        )
        return expenses

    def select_by_year(self, user_id: int, year: int) -> list[Expenses]:
        expenses = (
            self.session.query(Expenses)
            .filter(Expenses.user_id == user_id)
            .filter(extract('year', Expenses.date) == year)
            .all()
        )
        return expenses

    def update(self, user_id: int, expense_id: int, expense: Expenses) -> None:
        (
            self.session.query(Expenses)
            .filter(Expenses.user_id == user_id)
            .filter(Expenses.id == expense_id)
            .update({
                "value": expense.value,
                "type": expense.type,
                "originType": expense.originType,
                "recurrence_type": expense.recurrence_type,
                "date": expense.date,
            })
        )
        self.session.commit()