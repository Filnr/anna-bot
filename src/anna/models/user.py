from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    verified: Mapped[bool] = mapped_column(default=False)
    added_at: Mapped[datetime] = mapped_column(default=func.now())
    role: Mapped[str] = mapped_column(String(10))

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, verified={self.verified!r}, added_at={self.added_at!r}, role={self.role!r})"
