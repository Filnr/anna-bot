from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    cpf: Mapped[Optional[str]] = mapped_column(String(11), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())
    free_access: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, access={self.free_access!r}, added_at={self.added_at!r})"

class Subscription(Base):
    __tablename__ = "subscriptions"

    #Informações do usuario
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    #Informações do plano
    plan: Mapped[str] = mapped_column(String(50))
    plan_recurrence: Mapped[str] = mapped_column(String(10), default="monthly")
    status: Mapped[str] = mapped_column(String(10))
    started_at: Mapped[datetime] = mapped_column()
    current_period_end: Mapped[datetime] = mapped_column()
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # id do gateway de pagamento
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)