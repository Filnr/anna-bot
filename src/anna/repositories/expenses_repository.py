from sqlalchemy import except_, select
from core.database import Base
from models.expenses import Expenses
from sqlalchemy.orm import Session
from typing import Optional, Any, Sequence


def create(db: Session, expenses: Expenses) -> Expenses:
    try:
        db.add(expenses)
        db.commit()
        db.refresh(expenses)
        return expenses
    except Exception as e:
        db.rollback()
        raise e

def get_by_owner_and_name(db: Session, expense_name: str, user_id: int) -> type[Expenses] | None:
    return db.query(Expenses).filter(Expenses.user_id == user_id).filter(Expenses.name == expense_name).first()

def delete(db: Session, expenses: Expenses) -> None:
    db.delete(expenses)
    db.commit()
