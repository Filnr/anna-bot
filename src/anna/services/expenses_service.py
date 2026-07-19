from core.database import SessionLocal, init_db
from models.expense import Expenses
from repositories.expenses_repository import ExpensesRepository

class ExpensesService:
    def __init__(self, repository: ExpensesRepository) -> None:
        self.repository = repository

    def register(self,expense: Expenses) -> None:
        #Registra as despesas
        self.repository.create(expense)

    def read_month(self, user_id: int, month: int) -> Expenses:
        return self.repository.select_by_month(user_id, month)

    def update(self,user_id: int, expense_id: int, expense: Expenses) -> None:
        self.repository.update(user_id, expense_id, expense)

    def read_last_month_by_type(self, user_id: int, type: str) -> Expenses:
        return self.repository.select_last_month_by_type(user_id, type)
