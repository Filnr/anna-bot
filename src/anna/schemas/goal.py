from typing import Literal
from pydantic import BaseModel, Field

class GoalDTO(BaseModel):
    name: str
    type: str
    value: float = Field(gt=0)
    accumulated_value: float = Field(gt=0)
    period: Literal["weekly", "monthly", "quarterly", "yearly"]