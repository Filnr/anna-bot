from typing import Literal
from pydantic import BaseModel, Field

class ExpenseDTO(BaseModel):
    value: float = Field(gt=0)
    name: str
    category: str
    recurrence_type: Literal["monthly", "annual", "weekly", "only-time"]
    installment: int
    total_installment: int
