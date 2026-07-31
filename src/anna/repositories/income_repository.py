from typing import Sequence
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, NoResultFound
from models.income import Income
from sqlalchemy.orm import Session
from core.exceptions import DatabaseUnavailableError, IncomeCantBeDeletedError, IncomeDoesNotExistError, IncomeAlreadyExistsError

class IncomeRepository:
    def __init__(self, session: Session):
        self.session: Session = session

    def create(self, user_id: int, income: Income) -> Income:
       try:
           self.session.add(income)
           self.session.commit()
           self.session.refresh(income)
           return income
       except IntegrityError as e:
           self.session.rollback()
           raise IncomeAlreadyExistsError("Income violates a unique constraint") from e
       except OperationalError as e:
           self.session.rollback()
           raise DatabaseUnavailableError("Could not reach the database") from e

    def update(self, old_income_name: str, new_income: Income, user_id: int) -> Income:
        try:
            income = self.session.execute(select(Income).where(Income.user_id == user_id, Income.name == old_income_name)).scalar_one()
        except NoResultFound as e:
            raise IncomeDoesNotExistError("Income does not exist") from e

        income.name = new_income.name
        income.target_value = new_income.value
        income.origin = new_income.origin
        income.recurrence_type = new_income.recurrence_type

        try:
            self.session.commit()
            self.session.refresh(income)
            return income
        except IntegrityError as e:
            self.session.rollback()
            raise IncomeAlreadyExistsError("Income violates a unique constraint") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

    def delete(self, income_name: str, user_id: int) -> bool:
        try:
            income = self.session.execute(select(Income).where(Income.user_id == user_id, Income.name == income_name)).scalar_one()
        except NoResultFound as e:
            raise IncomeDoesNotExistError("Income does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e

        try:
            self.session.delete(income)
            self.session.commit()
            return True
        except IntegrityError as e:
            self.session.rollback()
            raise IncomeAlreadyExistsError("Income violates a unique constraint") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

    def select_all(self, user_id: int) -> Sequence[Income]:
        try:
            income = self.session.execute(select(Income).where(Income.user_id == user_id)).scalars().all()
            return income
        except NoResultFound as e:
            raise IncomeDoesNotExistError("Income does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e

    def select_by_name(self, user_id: int, income_name: str) -> Income:
        try:
            income = self.session.execute(select(Income).where(Income.user_id == user_id, Income.name == income_name)).scalar_one()
            return income
        except NoResultFound as e:
            raise IncomeDoesNotExistError("Income does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e

    def select_by_recurrence(self, user_id: int, recurrence_type: str) -> Income:
        try:
            income = self.session.execute(select(Income).where(Income.user_id == user_id, Income.name == recurrence_type)).scalar_one()
            return income
        except NoResultFound as e:
            raise IncomeDoesNotExistError("Income does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e

    def select_by_id(self, user_id: int, income_id: int) -> Income:
        try:
            income = self.session.execute(select(Income).where(Income.user_id == user_id, Income.id == income_id)).scalar_one()
            return income
        except NoResultFound as e:
            raise IncomeDoesNotExistError("Income does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e


