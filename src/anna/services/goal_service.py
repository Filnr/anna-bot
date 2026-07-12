from core.database import SessionLocal, init_db
from models.goal import Goal
import repositories.goal_repository
from schemas.goal import GoalDTO
from datetime import datetime

class GoalService:
    def __init__(self, repository: repositories.GoalRepository):
        self.repository = repository

    def create(self, userid: int, data: GoalDTO) -> Goal:
        goal = Goal(
            name=data.name,
            userId=userid,
            type=data.type,
            value=data.value,
            period=data.period,
            created_at=datetime.now()
        )
        return self.repository.create(goal)

    def update(self, userId: int, old_name_goal: str,goal: GoalDTO) -> Goal:
        if goal.value <= 0:
            raise Exception(f"Goal value {goal.value} is less than 0")
        correct_period = goal.period == 'monthly' or goal.period == 'yearly'
        if not correct_period:
            raise Exception(f"Goal period {goal.period} is not valid")
        return self.repository.update(userId, old_name_goal, goal)

