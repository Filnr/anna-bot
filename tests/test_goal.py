from services.goal_service import GoalService
from unittest.mock import Mock
from schemas.goal import GoalDTO
from repositories.goal_repository import GoalRepository
from core.database import SessionLocal
from models.user import User

data = GoalDTO(
    name="Test",
    type="c",
    value=10000,
    accumulated_value=0,
    period="once",
)
user_id = 1

def test_create_create():
    # arrange
    db = SessionLocal()
    rp = GoalRepository(db)
    service = GoalService(rp)
    resultado = service.create(user_id, data)
    assert resultado.name == "Test"
    assert resultado.target_value == 10000
    assert resultado.accumulated_value == 0
    assert resultado.period == "once"

    resultado = service.select_goal(user_id, data.name)
    assert resultado.type == "c"

    update = GoalDTO(
        name="Testando",
        type="e",
        value=10000,
        accumulated_value=0,
        period="once",
    )

    resultado = service.update(user_id, data.name, update)
    assert resultado.name == "Testando"
    assert resultado.target_value == 50000
    assert resultado.accumulated_value == 0


    resultado = service.delete(user_id, update.name)
    assert resultado == True
    db.close()


