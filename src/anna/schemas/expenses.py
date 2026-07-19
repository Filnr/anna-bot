from typing import Literal
from pydantic import BaseModel, Field

class Expenses(BaseModel):
    value: float = Field(gt=0)
    name: str
    type: str
    recurrence_type: Literal["monthly", "annual", "weekly", "only-time"]