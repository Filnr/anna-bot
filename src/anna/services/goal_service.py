from typing import List
from core.database import SessionLocal, init_db
from models.goal import Goal
from repositories.goal_repository import GoalRepository
from schemas.goal import GoalDTO
from datetime import datetime

class GoalService:
    def __init__(self, repository: GoalRepository):
        self.repository = repository

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        self.repository.session.close()

    def create(self, userid: int, data: GoalDTO) -> Goal:
        goal = Goal(
            name=data.name,
            userId=userid,
            type=data.type,
            target_value=data.value,
            accumulated_value=data.accumulated_value,
            period=data.period,
        )
        return self.repository.create(goal)

    def update(self, user_id: int, old_name_goal: str, data: GoalDTO) -> Goal:
        goal = Goal(
            name=data.name,
            userId=user_id,
            type=data.type,
            target_value=data.value,
            period=data.period,
            accumulated_value=data.accumulated_value,
        )
        return self.repository.update(user_id, old_name_goal, goal)

    def delete(self, userId: int, goal_name: str) -> bool:
        return self.repository.delete(userId, goal_name)

    def contribute(self, user_id: int, goal_name: str, amount: float) -> Goal:
        goal = self.repository.select_name(goal_name, user_id)
        new_accumulated_value = goal.accumulated_value + amount
        return self.repository.insert_accumulated_value(user_id, goal_name, new_accumulated_value)

    def select_all(self, userId: int) -> list[Goal]:
        return self.repository.select_all(userId)

    def select_latest(self, userId: int) -> Goal:
        return self.repository.select_latest(userId)

    def select_goal(self, user_id: int, goal_name: str) -> Goal:
        return self.repository.select_name(goal_name, user_id)

