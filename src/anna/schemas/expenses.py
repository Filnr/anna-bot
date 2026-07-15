from typing import Literal
from pydantic import BaseModel, Field

class GoalDTO(BaseModel):
    value: float = Field(gt=0)
    name: str
    type: str
    recurrence_type: Literal["monthly", "annual", "weekly", "only-time"]