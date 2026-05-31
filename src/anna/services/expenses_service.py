from core.database import SessionLocal, init_db
from models.expenses import Expenses
from repositories.expenses_repository import ExpensesRepository

class ExpensesService:
    def __init__(self, repository: ExpensesRepository) -> None:
        self.repository = repository

        def register(self,expense: Expenses) -> None:
            #Registra as despesas
            self.repository.create(expense)

        def read_month(self, user_id: int, month: int) -> Expenses:
            return self.repository.read_month(user_id, month)

        def update(self, expense: Expenses) -> None:
            self.repository.update(expense)
