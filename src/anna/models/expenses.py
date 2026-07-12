from datetime import datetime
from sqlalchemy import ForeignKey, String, Float, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class Expenses(Base):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String)
    originType: Mapped[str] = mapped_column(String)
    date: Mapped[datetime] = mapped_column(default=func.now())
    recurrence_type: Mapped[str] = mapped_column(String(20), default="only-time")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))