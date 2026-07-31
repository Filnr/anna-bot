from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, NoResultFound
from models.goal import Goal
from sqlalchemy.orm import Session
from core.exceptions import DatabaseUnavailableError, GoalAlreadyExistsError, GoalDoesNotExistError, GoalCantBeDeletedError

class GoalRepository:
    def __init__(self, session: Session):
        self.session: Session = session

    def _get_goal_by_name(self, user_id, goal_name: str) -> Goal:
        try:
            goal = self.session.execute(
                select(Goal).where(
                    Goal.userId == user_id,
                    Goal.name == goal_name
                )
            ).scalar_one()
        except NoResultFound:
            raise GoalDoesNotExistError("Goal does not exist")

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

    def update(self, user_id: int, old_goal_name: str ,goal: Goal) -> Goal:
        goal_old = self._get_goal_by_name(user_id, old_goal_name)

        goal_old.name = goal.name
        goal_old.type = goal.type
        goal_old.target_value = goal.target_value
        goal_old.period = goal.period
        return self._commit_update(goal_old)

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

    def select_name(self, goal_name: str, user_id: int):
        goal = self._get_goal_by_name(user_id, goal_name)
        return goal

    def select_latest(self, user_id: int) -> Goal:
        try:
            goal = self.session.execute(select(Goal).where(Goal.userId == user_id)).scalars().one()
        except NoResultFound:
            raise GoalDoesNotExistError("There are no goals")
        return goal


    def delete(self, user_id: int, goal_name: str) -> bool:
        goal = self._get_goal_by_name(user_id, goal_name)

        try:
            self.session.delete(goal)
            self.session.commit()
            return True
        except IntegrityError as e:
            self.session.rollback()
            raise GoalCantBeDeletedError("Goal cannot be deleted because it has related records") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

    def insert_accumulated_value(self, user_id: int, goal_name: str, value: float) -> Goal:
        goal = self._get_goal_by_name(user_id, goal_name)

        goal.accumulated_value = value

        return self._commit_update(goal)

    def _commit_update(self, goal: Goal) -> Goal:
        try:
            self.session.commit()
            self.session.refresh(goal)
            return goal
        except IntegrityError as e:
            self.session.rollback()
            raise GoalAlreadyExistsError("Goal violates a unique constraint") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e
