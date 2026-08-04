from typing import Literal
from pydantic import BaseModel, Field, EmailStr

class UserCreateDTO(BaseModel):
    telegram_id: int
    name: str

class UserUpdateBillingDTO(BaseModel):
    cpf: str = Field(min_length=11, max_length=11)
    email: EmailStr

class SubscriptionDTO(BaseModel):
    plan: str
    plan_recurrence: Literal["monthly", "annual", "weekly"]
