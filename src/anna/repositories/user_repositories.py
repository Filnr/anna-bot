from typing import Sequence
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, NoResultFound
from sqlalchemy.sql.functions import current_user

from models.user import User, Subscription
from sqlalchemy.orm import Session
from core.exceptions import (UserCreationError, UserAlreadyExistsError, UserDoesNotExistError, DatabaseUnavailableError,
                             SubscriptionAlreadyExistsError, SubscriptionDoesNotExistError, SubscriptionCantBeDeletedError)


class UserRepository:
    def __init__(self, session: Session):
        self.session: Session = session

    def __find_user_by_id(self, telegram_id: int) -> User:
        try:
             user = self.session.execute(
                 select(User).where(
                     User.telegram_id == telegram_id
                 )
             ).scalar_one()
             return user
        except NoResultFound as e:
            raise UserDoesNotExistError("User does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e

    def create(self, user: User) -> User:
        try:
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
        except IntegrityError as e:
            self.session.rollback()
            raise UserAlreadyExistsError("User already exists") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

    def update(self, telegram_id: int, user: User) -> User:
        old_user = self.__find_user_by_id(telegram_id)

        old_user.telegram_id = user.telegram_id
        old_user.cpf = user.cpf
        old_user.email = user.email
        old_user.name = user.name
        old_user.free_access = user.free_access

        try:
            self.session.commit()
            self.session.refresh(old_user)
            return old_user
        except IntegrityError as e:
            self.session.rollback()
            raise UserAlreadyExistsError("User already exists") from e
        except OperationalError as e:
            self.session.rollback()
            raise DatabaseUnavailableError("Could not reach the database") from e

    def delete(self, telegram_id: int) -> bool:
        user = self.__find_user_by_id(telegram_id)

        try:
            self.session.delete(user)
            self.session.commit()
            return True
        except IntegrityError as e:
            self.session.rollback()
            raise UserDoesNotExistError("User cant be deleted") from e
        except OperationalError as e:
            self.session.rollback()
        return False

    def select_by_id(self, user_id: int) -> User:
        return self.__find_user_by_id(user_id)

    def select_by_cpf(self, cpf: str) -> User:
        try:
            user = self.session.execute(
                select(User).where(
                    User.cpf == cpf
                )
            ).scalar_one()
            return user
        except NoResultFound as e:
            raise UserDoesNotExistError("User does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e

    def select_by_email(self, email: str) -> User:
        try:
            user = self.session.execute(
                select(User).where(
                    User.email == email
                )
            ).scalar_one()
            return user
        except NoResultFound as e:
            raise UserDoesNotExistError("User does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e

    def select_by_telegram_id(self, telegram_id: int) -> User:
        try:
            user = self.session.execute(
                select(User).where(
                    User.telegram_id == telegram_id
                )
            ).scalar_one()
            return user
        except NoResultFound as e:
            raise UserDoesNotExistError("User does not exist") from e
        except OperationalError as e:
            raise DatabaseUnavailableError("Could not reach the database") from e
