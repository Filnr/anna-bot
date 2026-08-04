from typing import Sequence
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, NoResultFound
from models.user import User, Subscription
from sqlalchemy.orm import Session
from core.exceptions import (DatabaseUnavailableError,
                             SubscriptionAlreadyExistsError, SubscriptionDoesNotExistError, SubscriptionCantBeDeletedError)

class SubscriptionRepository:
    def __init__(self, session: Session):
        self.session: Session = session

    def __find_subs_by_id(self, subs_id: int, user_id: int) -> User:
        try:
            subs = self.session.execute(
                select(Subscription).where(
                    Subscription.id == subs_id,
                    Subscription.user_id == user_id
                )
            ).scalar_one()
            return subs
        except NoResultFound as e:
            raise SubscriptionDoesNotExistError("Subscription does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e

    def create(self, subscription: Subscription) -> Subscription:
        try:
            self.session.add(subscription)
            self.session.commit()
            self.session.refresh(subscription)
            return subscription
        except IntegrityError as e:
            self.session.rollback()
            raise SubscriptionAlreadyExistsError("Subscription already exists") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

    def update(self, subscription_id: int, user_id: int, subscription: Subscription) -> Subscription:
        subs = self.__find_subs_by_id(subscription_id, user_id)
        subs.plan = subscription.plan
        subscription.plan_recurrence = subscription.plan_recurrence
        subscription.cancelled_at = subscription.cancelled_at
        subscription.status = subscription.status
        try:
            self.session.commit()
            self.session.refresh(subscription)
            return subscription
        except IntegrityError as e:
            self.session.rollback()
            raise SubscriptionAlreadyExistsError("Subscription already exists") from e
        except OperationalError as e:
            self.session.rollback()