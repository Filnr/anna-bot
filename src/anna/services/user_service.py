from sqlalchemy import true
from sqlalchemy.exc import NoResultFound

from core.database import SessionLocal, init_db
from models.user import User
from repositories.user_repositories import UserRepository
from schemas.user import UserCreateDTO
from core.exceptions import UserDoesNotExistError


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def __enter__(self):
        return self

    def close(self) -> None:
        self.repository.session.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


    def create(self, data: UserCreateDTO) -> User:
        user = User(
            telegram_id=data.telegram_id,
            name=data.name,
        )
        return self.repository.create(user)

    # Function responsible for usability
    def has_access(self, telegram_id: int) -> bool:
        user = self.repository.select_by_id(telegram_id)
        return user.free_access

    def find_by_name(self, telegram_id: int) -> str:
        user = self.repository.select_by_id(telegram_id)
        return user.name

    def is_registered(self, telegram_id: int) -> bool:
        try:
            self.repository.select_by_id(telegram_id)
            return True
        except UserDoesNotExistError:
            return False

    def find_by_telegram_id(self, telegram_id: int) -> User:
        return self.repository.select_by_id(telegram_id)


def get_user_service() -> UserService:
    session = SessionLocal()
    repository = UserRepository(session)
    return UserService(repository)
