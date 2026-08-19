import datetime
from typing import Sequence, List
from sqlalchemy import select, extract
from sqlalchemy.exc import IntegrityError, OperationalError
from core.exceptions import ExpenseAlreadyExistsError, ExpenseDoesNotExistError, ExpenseCantBeDeletedError, \
    DatabaseUnavailableError, ExpenseCreationError
from models.expense import Expense
from sqlalchemy.orm import Session
from dateutil.relativedelta import relativedelta


class ExpensesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _get_expenses_by_id(self, user_id: int, expense_id: int) -> Expense:
        try:
            expenses = self.session.execute(
                select(Expense).where(
                    Expense.user_id == user_id,
                    Expense.id == expense_id
                )
            ).scalar_one()
            return expenses
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseDoesNotExistError("Expense does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e


    def create(self, expense: Expense) -> Expense:
        try:
            self.session.add(expense)
            self.session.commit()
            self.session.refresh(expense)
            return expense
        except IntegrityError as e:
            raise ExpenseAlreadyExistsError("Expense violates a unique constraint") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e

    def _commit_and_refresh_many(self, expenses: List[Expense]) -> List[Expense]:
        try:
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseCreationError("One or more expenses violate a constraint") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

        for expense in expenses:
            self.session.refresh(expense)

        return expenses

    def create_many(self, expenses: List[Expense])-> Sequence[Expense]:
        self.session.add_all(expenses)
        return self._commit_and_refresh_many(expenses)

    def select_by_month(self, user_id: int, month: int, year: int | None = None) -> Sequence[Expense]:
        if year is None:
            year = datetime.datetime.now().year
        try:
            expenses = self.session.execute(
                select(Expense).where(
                    Expense.user_id == user_id,
                    extract('month', Expense.date) == month,
                    extract('year', Expense.date) == year,
                )
            ).scalars().all()
            return expenses
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseDoesNotExistError("Expense does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e

    def select_last_month_by_category(self, user_id: int, category: str) -> Sequence[Expense]:
        last_month = datetime.datetime.now() - relativedelta(months=1)
        try:
            expenses = self.session.execute(
                select(Expense).where(
                    Expense.user_id == user_id,
                    Expense.date >= last_month,
                    Expense.category == category,
                )

            ).scalars().all()
            return expenses
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseDoesNotExistError("Expense does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e


    def select_by_id(self, user_id: int, expense_id: int) -> Expense:
        return self._get_expenses_by_id(user_id, expense_id)

    def select_by_year(self, user_id: int, year: int) -> Sequence[Expense]:
        try:
            expenses = self.session.execute(
                select(Expense).where(
                    Expense.user_id == user_id,
                    extract('year', Expense.date) == year,
                )
            ).scalars().all()
            return expenses
        except IntegrityError as e:
            self.session.rollback()
            raise ExpenseDoesNotExistError("Expense does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e

    def update(self, user_id: int, expense_id: int, new_expense: Expense) -> Expense:
        old_expense = self._get_expenses_by_id(user_id, expense_id)

        old_expense.category = new_expense.category
        old_expense.value = new_expense.value
        old_expense.installment = new_expense.installment
        old_expense.name = new_expense.name
        old_expense.total_installment = new_expense.total_installment
        old_expense.recurrence_type = new_expense.recurrence_type

        try:
            self.session.commit()
            self.session.refresh(old_expense)
            return old_expense
        except IntegrityError as e:
            raise ExpenseAlreadyExistsError("Expense violates a unique constraint") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e

    def delete(self, user_id: int, expense_id: int) -> None:
        expense = self._get_expenses_by_id(user_id, expense_id)
        try:
            self.session.delete(expense)
            self.session.commit()
        except IntegrityError as e:
            raise ExpenseDoesNotExistError("Expense cant be deleted") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not connect to the database") from e





