from datetime import datetime
from typing import List, Sequence
from dateutil.relativedelta import relativedelta
from models.expense import Expense
from repositories.expense_repository import ExpensesRepository
from schemas.expenses import ExpenseDTO

class ExpensesService:
    def __init__(self, repository: ExpensesRepository) -> None:
        self.repository = repository

    def create(self, user_id: int, data: ExpenseDTO) -> List[Expense]:
        date_now = datetime.now()
        installment_value = round(data.value / data.total_installment, 2)

        expenses = [
            Expense(
                user_id=user_id,
                value=installment_value,
                category=data.category,
                name=data.name,
                date=date_now + relativedelta(months=i),
                installment=i + 1,
                total_installment=data.total_installment,
                recurrence_type=data.recurrence_type,
            )
            for i in range(data.total_installment)
        ]

        return self.repository.create_many(expenses)

    def update(self, user_id: int, expense_id: int, data: ExpenseDTO) -> Expense:
        expense = Expense(
            user_id=user_id,
            value=data.value,
            category=data.category,
            name=data.name,
            installment=data.installment,
            total_installment=data.total_installment,
            recurrence_type=data.recurrence_type,
            date=datetime.now(),
        )
        return self.repository.update(user_id, expense_id, expense)

    def delete(self, user_id: int, expense_id: int) -> None:
        self.repository.delete(user_id, expense_id)

    def select_by_id(self, user_id: int, expense_id: int) -> Expense:
        return self.repository.select_by_id(user_id, expense_id)

    def select_by_last_month(self, user_id: int) -> Sequence[Expense]:
        month = (datetime.now() - relativedelta(months=1)).month
        return self.repository.select_by_month(user_id, month)

    def select_by_month(self, user_id: int, month: int) -> Sequence[Expense]:
        return self.repository.select_by_month(user_id, month)

    def select_by_category_last_month(self, user_id, category: str) -> Sequence[Expense]:
        return self.repository.select_last_month_by_category(user_id, category)

