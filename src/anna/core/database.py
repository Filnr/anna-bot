import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine - gerenciador de conexão com banco
engine = create_engine(DATABASE_URL)

# SessionLocal - factory para criar sessões
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Cria todas as tabelas baseado nos modelos"""
    Base.metadata.create_all(engine)