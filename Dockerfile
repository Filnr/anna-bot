# 1. Usar uma imagem leve do Python
FROM python:3.11-slim

# 2. Configurar variáveis de ambiente para o Python e Poetry
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

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

# 6. Instalar as dependências do projeto (sem as de desenvolvimento)
RUN poetry install --no-interaction --no-ansi --no-root --without dev

# 7. Copiar o restante do código do seu projeto para dentro do container
COPY . .

# 8. Comando para rodar o bot
# Notei que seu código está dentro de src/anna/services/...
# Altere o caminho abaixo para o arquivo exato que você roda para ligar o bot (ex: src/anna/bot.py)
CMD ["python", "src/anna/bot/bot.py"]