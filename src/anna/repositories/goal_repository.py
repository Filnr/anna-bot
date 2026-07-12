from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, NoResultFound
from models.goal import Goal
from sqlalchemy.orm import Session
from core.exceptions import DatabaseUnavailableError, GoalAlreadyExistsError, GoalDoesNotExistError, GoalCantBeDeletedError
from schemas.goal import GoalDTO

class GoalRepository:
    def __init__(self, session: Session):
        self.session: Session = session

    def create(self, goal: Goal) -> Goal:
        try:
            self.session.add(goal)
            self.session.commit()
            self.session.refresh(goal)
            return goal
        except IntegrityError as e:
            self.session.rollback()
            raise GoalAlreadyExistsError("Goal violates a unique constraint") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

    def update(self, user_id: int, old_goal_name: str ,goal: GoalDTO) -> Goal:
        try:
            goal_old = self.session.execute(select(Goal).where(Goal.userId == user_id, Goal.name == old_goal_name)).scalar_one()
        except NoResultFound:
            raise GoalDoesNotExistError("Goal does not exist")

        goal_old.name = goal.name
        goal_old.type = goal.type
        goal_old.value = goal.value
        goal_old.period = goal.period
        try:
            self.session.commit()
            self.session.refresh(goal_old)
        except IntegrityError as e:
            self.session.rollback()
            raise GoalAlreadyExistsError("Goal violates a unique constraint") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

        return goal_old

    def select_all(self, user_id: int):
        try:
            goals = self.session.execute(select(Goal).filter(Goal.userId == user_id)).scalars().all()
        except NoResultFound:
            raise GoalDoesNotExistError("Goal does not exist")
        return goals

    def select_id(self, goalId: int):
        try:
            goal = self.session.get(Goal, goalId)
        except NoResultFound:
            raise GoalDoesNotExistError("Goal does not exist")
        return goal

    def select_name(self, goalName: str, userId: int):
        try:
            goal = self.session.execute(select(Goal).filter(Goal.userId == userId).filter(Goal.name == goalName)).scalar_one()
        except NoResultFound:
            raise GoalDoesNotExistError("Goal does not exist")
        return goal

    def delete(self, user_id: int, goal_name: str) -> None:
        try:
            goal = self.session.execute(select(Goal).where(Goal.userId == user_id, Goal.name == goal_name)).scalar_one()
        except NoResultFound:
            raise GoalDoesNotExistError("Goal does not exist")

        try:
            self.session.delete(goal)
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise GoalCantBeDeletedError("Goal cannot be deleted because it has related records") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e
