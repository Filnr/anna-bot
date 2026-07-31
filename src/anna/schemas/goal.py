from typing import Literal
from pydantic import BaseModel, Field

class GoalDTO(BaseModel):
    name: str
    type: Literal["e", "c"]
    value: float = Field(gt=0)
    accumulated_value: float = Field(ge=0)
    period: Literal["weekly", "monthly", "quarterly", "yearly", "once"]