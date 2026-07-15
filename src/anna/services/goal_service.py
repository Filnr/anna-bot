from typing import List
from core.database import SessionLocal, init_db
from models.goal import Goal
from repositories.goal_repository import GoalRepository
from schemas.goal import GoalDTO
from datetime import datetime

class GoalService:
    def __init__(self, repository: GoalRepository):
        self.repository = repository

    def create(self, userid: int, data: GoalDTO) -> Goal:
        goal = Goal(
            name=data.name,
            userId=userid,
            type=data.type,
            value=data.value,
            period=data.period,
        )
        return self.repository.create(goal)

    def update(self, userId: int, old_name_goal: str,goal: GoalDTO) -> Goal:
        return self.repository.update(userId, old_name_goal, goal)

    def delete(self, userId: int, goal_name: str) -> None:
        return self.repository.delete(userId, goal_name)

    def select_all(self, userId: int) -> list[Goal]:
        return self.repository.select_all(userId)

    def select_latest(self, userId: int) -> Goal:
        return self.repository.select_latest(userId)

    def select_goal(self, user_id: int, goal_name: str) -> Goal:
        return self.repository.select_goal(user_id,goal_name)

