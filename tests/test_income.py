from src.anna.services.income_service import IncomeService
from unittest.mock import Mock
from schemas.income import IncomeDTO
from repositories.income_repository import IncomeRepository
from core.database import SessionLocal
from models.user import User

data = IncomeDTO(
    name="Teste",
    value=20000,
    origin="CLT",
    recurrence_type="monthly",
)
user_id = 1

def test_create_create():
    # arrange
    db = SessionLocal()
    rp = IncomeRepository(db)
    service = IncomeService(rp)
    resultado = service.create(user_id, data)
    assert resultado.name == "Teste"
    assert resultado.value == 20000
    assert resultado.origin == "CLT"
    assert resultado.recurrence_type == "monthly"

    resultado = service.select_by_name(user_id, data.name)
    assert resultado.value == 20000
    assert resultado.origin == "CLT"
    assert resultado.recurrence_type == "monthly"

    resultado = service.select_by_id(user_id, resultado.id)
    assert resultado.value == 20000
    assert resultado.origin == "CLT"
    assert resultado.recurrence_type == "monthly"
    assert resultado.name == resultado.name

    update = IncomeDTO(
        name="Test",
        value=50000,
        origin="PJ",
        recurrence_type="monthly",
    )
    resultado = service.update(user_id, data.name, update)
    assert resultado.name == "Test"
    assert resultado.value == 50000
    assert resultado.origin == "PJ"
    assert resultado.recurrence_type == "monthly"

    resultado = service.delete(user_id, update.name)
    assert resultado == True
    db.close()


