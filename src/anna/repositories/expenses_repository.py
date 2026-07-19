import datetime
from typing import Sequence

from sqlalchemy import select, extract
from sqlalchemy.exc import IntegrityError, OperationalError
from core.exceptions import ExpenseAlreadyExistsError, ExpenseDoesNotExistError, ExpenseCantBeDeletedError, \
    DatabaseUnavailableError
from models.expense import Expenses
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta


class ExpensesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, expense: Expenses) -> Expenses:
        try:
            self.session.add(expense)
            self.session.commit()
            self.session.refresh(expense)
            return expense
        except IntegrityError as e:
            raise ExpenseAlreadyExistsError("Expense violates a unique constraint") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e

    def select_by_month(self, user_id: int, month: int, year: int) -> Sequence[Expenses]:
        if year is None:
            year = datetime.datetime.now().year
        try:
            expenses = self.session.execute(
                select(Expenses).where(
                    Expenses.user_id == user_id,
                    extract('month', Expenses.date) == month,
                    extract('year', Expenses.date) == year,
                )
            ).scalars().all()
            return expenses
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseDoesNotExistError("Expense does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e


    def select_last_month_by_type(self, user_id: int, type: str) -> Sequence[Expenses]:
        last_month = datetime.datetime.now() - relativedelta(months=1)
        try:
            expenses = self.session.execute(
                select(Expenses).where(
                    Expenses.user_id == user_id,
                    Expenses.category == type,
                    Expenses.date >= last_month
                )

            ).scalars().all()
            return expenses
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseDoesNotExistError("Expense does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e


    def select_by_id(self, user_id: int, expense_id: int) -> Expenses:
        try:
            expenses = self.session.execute(
                select(Expenses).where(
                    Expenses.user_id == user_id,
                    Expenses.id == expense_id
                )
            ).scalar_one()
            return expenses
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseDoesNotExistError("Expense does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e

    def select_by_year(self, user_id: int, year: int) -> Sequence[Expenses]:
        try:
            expenses = self.session.execute(
                select(Expenses).where(
                    Expenses.user_id == user_id,
                    extract('year', Expenses.date) == year,
                )
            ).scalars().all()
            return expenses
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseDoesNotExistError("Expense does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e

    def update(self, user_id: int, expenses, expense: Expenses) -> Expenses:
        try:

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