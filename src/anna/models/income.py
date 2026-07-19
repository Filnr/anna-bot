from datetime import datetime
from sqlalchemy import ForeignKey, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class Income(Base):
    __tablename__ = "incomes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    value: Mapped[float] = mapped_column(default=0)
    origin: Mapped[str] = mapped_column(String(100))
    recurrence_type: Mapped[str] = mapped_column(String(20), default="monthly")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    date: Mapped[datetime] = mapped_column(server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("name", "user_id", name="uq_income_name_user"),
    )