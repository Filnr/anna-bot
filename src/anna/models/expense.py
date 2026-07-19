from datetime import datetime
from sqlalchemy import ForeignKey, String, Float, func, Integer
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class Expense(Base):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    date: Mapped[datetime] = mapped_column()
    installment: Mapped[int] = mapped_column(Integer, default=1)
    total_installment: Mapped[int] = mapped_column(Integer, default=1)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())