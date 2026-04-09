from core.database import SessionLocal, init_db
from models.expenses import Expenses
import repositories.expenses_repository

db = SessionLocal()
repositories = repositories.expenses_repository

def register(value: float, type: str, otype: str, recurrence: str, user_id: int) -> Expenses:
    expense = Expenses(
        value=value,
        type=type,
        originType=otype,
        recurrence_type=recurrence,
        user_id=user_id
    )
    repositories.create(db, expense)


