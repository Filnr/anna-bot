from sqlalchemy import true

from core.database import SessionLocal, init_db
from models.user import User
import repositories.user_repositories

db = SessionLocal()
user_repositories = repositories.user_repositories

def register_user(telegram_id: int, name: str) -> User:
    # Cria uma sessão nova apenas para esta operação
    with SessionLocal() as db:
        try:
            # Verifica se o ID já existe
            existing_user = user_repositories.get_user_by_id(db, telegram_id)

            if not existing_user:
                new_user = User(
                    id=telegram_id,
                    name=name,
                    role="Admin",  # Você pode mudar para "user" depois
                    added_by=1
                )
                return user_repositories.create_user(db, new_user)

            return existing_user
        except Exception as e:
            db.rollback()  # Desfaz qualquer erro para não travar o banco
            print(f"Erro ao registrar usuário: {e}")
            raise e

def get_name(telegram_id: int) -> str:
    with SessionLocal() as db:
        existing_user = user_repositories.get_user_by_id(db, telegram_id)
        if not existing_user:
            return "Nenhum User"
        return existing_user.name

def is_registered(telegram_id: int) -> bool:
    with SessionLocal() as db:
        existing_user = user_repositories.get_user_by_id(db, telegram_id)
        if not existing_user:
            return False
        return True
