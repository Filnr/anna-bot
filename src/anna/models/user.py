from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[str] = mapped_column(String(30), unique=True)
    added_at: Mapped[datetime] = mapped_column(server_default=func.now())
    role: Mapped[str] = mapped_column(String(10))
    free_acess: Mapped[bool] = mapped_column(server_default=func.false())

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, verified={self.free_acess!r}, added_at={self.added_at!r}, role={self.role!r})"

class Subscrition(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)