from sqlalchemy import except_, select
from core.database import Base
from models.user import User
from sqlalchemy.orm import Session
from typing import Optional, Any, Sequence

def create_user(db: Session, user: User) -> User:
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise e

def get_user(db: Session, user_name: str) -> type[User] | None:
    return db.query(User).filter(User.name == user_name).first()

def get_user_by_id(db: Session, user_id: int) -> type[User] | None:
    """

    :rtype: type[User] | None
    """
    return db.get(User, user_id)

def delete_user(db: Session, user_name: str) -> None:
    user = db.query(User).filter(User.name == user_name).first()
    db.delete(user)
    db.commit()

def delete_user_by_id(db: Session, user_id: int) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    db.delete(user)
    db.commit()

def verify_user(db: Session, new_user_id) -> type[User] | None:
    user = db.get(User, new_user_id)
    if user and not user.verified:
        user.verified = True # Altera direto no objeto
        db.commit()          # O SQLAlchemy percebe a mudança e faz o UPDATE pra você
        db.refresh(user)
        return user
    return None

def get_non_verified_user(db: Session, user_id: int) -> Sequence[Any] | None:
    stmt = select(User).where(User.verified == False)
    users = db.scalars(stmt).all()
    if not users:
        return None
    return users


def update_user(db: Session, user_name: str, new_user: User) -> type[User]:
    old_user = db.query(User).filter(User.name == user_name).first()
    if not old_user:
        raise Exception("User does not exist")
    excluded_fields = ['id', '_sa_instance_state']
    for key, value in new_user.__dict__.items():
        if key not in excluded_fields:
            setattr(old_user, key, value)
    # 3. Salva e atualiza
    db.commit()
    db.refresh(old_user)
    return old_user


