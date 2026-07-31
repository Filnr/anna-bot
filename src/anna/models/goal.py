from datetime import datetime
from sqlalchemy import ForeignKey, String, Float, func, Column
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class Goal(Base):
    __tablename__ = 'goal'
    id: Mapped[int] = mapped_column(primary_key=True)
    userId: Mapped[int] = mapped_column(ForeignKey('users.id'))

    name: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(2), default="e") # e = Economizar, C = comprar
    target_value: Mapped[float] = mapped_column(Float, default=0)
    accumulated_value: Mapped[float] = mapped_column(Float, default=0)
    period: Mapped[str] = mapped_column(String(20), default="Once")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())