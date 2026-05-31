import datetime
from sqlalchemy import except_, select, extract
from core.database import Base
from models.expenses import Expenses
from sqlalchemy.orm import Session
from typing import Optional, Any, Sequence

class ExpensesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

        def create(self, expense: Expenses) -> None:
            self.session.add(expense)
            self.session.commit()
            self.session.refresh(expense)

        def select_by_month(self, user_id: int, month: int, year: int = None) -> Expenses:
            if year is None:
                year = datetime.now().year

            expenses = (self.session.query(Expenses)
                        .filter(Expenses.user_id == user_id and extract('month', Expenses.date) == month and extract('year', Expenses.date) == year)
                        .all)
            return expenses

        def select_by_year(self, user_id: int, year: int) -> Expenses:
            expenses = self.session.select(Expenses).where(Expenses.user_id == user_id and extract('year', Expenses.date) == year)
            return expenses

