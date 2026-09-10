# 1. Usar uma imagem leve do Python (pyproject.toml exige >=3.13)
FROM python:3.13-slim

# 2. Configurar variáveis de ambiente para o Python e Poetry
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.4.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH="/app/src/anna"

# Adiciona o Poetry ao PATH do sistema
ENV PATH="$POETRY_HOME/bin:$PATH"

# 3. Instalar dependências do sistema necessárias (curl para instalar o Poetry)
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get purge -y --auto-remove curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Definir a pasta de trabalho dentro do container
WORKDIR /app

# 5. Copiar apenas os arquivos de configuração de dependências primeiro
# (Isso ajuda o Docker a buildar mais rápido se você não mudar as dependências)
COPY pyproject.toml poetry.lock ./

# 6. Instalar as dependências do projeto
# Não há grupo "dev" separado no pyproject.toml (pytest está junto das deps normais), então
# "--without dev" falha o build ("Group(s) not found: dev") — instala tudo mesmo.
RUN poetry install --no-interaction --no-ansi --no-root

# 7. Copiar o restante do código do seu projeto para dentro do container
COPY . .

# 8. Comando para rodar o bot
# O código importa módulos como "services.xxx" (sem prefixo "anna."), assumindo src/anna no
# sys.path — daí o PYTHONPATH definido acima. Sem ele, "python src/anna/bot/bot.py" falha com
# ModuleNotFoundError: No module named 'services' (só funciona sem essa env var dentro de uma
# IDE que marca src/anna como source root, ex. PyCharm).
CMD ["python", "src/anna/bot/bot.py"]