from core.database import SessionLocal
from models.income import Income
from repositories.income_repository import IncomeRepository
from schemas.income import IncomeDTO
from typing import Sequence

class IncomeService:
    def __init__(self, repository: IncomeRepository):
        self.repository = repository

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        self.repository.session.close()

    def create(self, user_id: int, data: IncomeDTO) -> Income:
        income = Income(
            name=data.name,
            value=data.value,
            origin=data.origin,
            recurrence_type=data.recurrence_type,
            user_id=user_id
        )
        return self.repository.create(income)

    def update(self, user_id: int, income_name: str, data: IncomeDTO) -> Income:
        income = Income(
            name=data.name,
            value=data.value,
            origin=data.origin,
            recurrence_type=data.recurrence_type
        )
        return self.repository.update(income_name, income, user_id)

    def delete(self, user_id: int, income_name: str) -> bool:
        return self.repository.delete(income_name, user_id)

    def select_all(self, user_id: int) -> Sequence[Income]:
        return self.repository.select_all(user_id)

    def select_by_id(self, user_id: int, income_id: int) -> Income:
        return self.repository.select_by_id(user_id, income_id)

    def select_by_name(self, user_id: int, income_name: str) -> Income:
        return self.repository.select_by_name(user_id, income_name)

    def select_by_recurrence_type(self, user_id: int, income_recurrence: str) -> Sequence[Income]:
        return self.repository.select_by_recurrence(user_id, income_recurrence)
