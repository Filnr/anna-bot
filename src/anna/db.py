from pathlib import Path
from core.database import SessionLocal, init_db
from models.user import User
from models.income import Income

# Inicializa o banco de dados
init_db()
print('✅ Banco de dados inicializado!')

# Cria uma sessão
with SessionLocal() as session:
    # Cria um novo usuário
    novo_usuario = User(
        name="Robisvaldo",
        added_by=1,  # obrigatório
        role="testador"
    )
    gasto_usuario = Income(
        income=1200.00,
        origin="Meu bolso",
        userId=1
    )

    # Adiciona à sessão
    session.add(novo_usuario)
    session.add(gasto_usuario)
    session.commit()

    print(f'✅ Usuário criado: {novo_usuario} e ganho: {gasto_usuario}')

    # Consulta todos os usuários
    usuarios = session.query(User).all()
    Incomes = session.query(Income).all()
    print(f'✅ Total de usuários: {len(usuarios)} e {len(Incomes)}')
