from core.database import SessionLocal, init_db
from models.expense import Expense
from repositories.expense_repository import ExpensesRepository

class ExpensesService:
    def __init__(self, repository: ExpensesRepository) -> None:
        self.repository = repository

    def register(self, expense: Expense) -> None:
        #Registra as despesas
        self.repository.create(expense)

    def read_month(self, user_id: int, month: int) -> Expense:
        return self.repository.select_by_month(user_id, month)

    def update(self, user_id: int, expense_id: int, expense: Expense) -> None:
        self.repository.update(user_id, expense_id, expense)

    def read_last_month_by_type(self, user_id: int, type: str) -> Expense:
        return self.repository.select_last_month_by_type(user_id, type)
