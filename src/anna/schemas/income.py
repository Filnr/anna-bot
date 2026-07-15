from typing import Literal
from pydantic import BaseModel, Field

class IncomeDTO(BaseModel):
    name: str
    value: float = Field(gt=0)
    origin: str = Field(max_length=100)
    recurrence_type: Literal["monthly", "annual", "weekly"]
