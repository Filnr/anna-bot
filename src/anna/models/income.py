from datetime import datetime
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class Income(Base):
    __tablename__ = "incomes"

    id: Mapped[int] = mapped_column(primary_key=True)
    income: Mapped[float] = mapped_column(default=0)
    origin: Mapped[str] = mapped_column(String(100))
    date: Mapped[datetime] = mapped_column(default=func.now())
    recurrence_type: Mapped[str] = mapped_column(String(20), default="monthly")
    userId: Mapped[int] = mapped_column(ForeignKey("users.id"))