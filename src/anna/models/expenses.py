from datetime import datetime
from sqlalchemy import ForeignKey, String, func, Column, Float
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class Expenses(Base):
    __tablename__ = 'expenses'

    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[float] = Column(Float)
    type: Mapped[str] = Column(String)
    originType: Mapped[str] = Column(String)
    date: Mapped[datetime] = mapped_column(default=func.now())
    recurrence_type: Mapped[str] = mapped_column(String(20), default="monthly")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

