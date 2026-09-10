import asyncio
from typing import Final
from pathlib import Path
from dotenv import load_dotenv
import os
import services.user_service
from core.database import init_db
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import services.expense_service
import services.llm_service as llm_service
from functools import wraps  # Importante: Biblioteca nativa do Python para criar o decorador
from services.user_service import UserService, get_user_service
from schemas.user import UserCreateDTO

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)
init_db()
print('O bot está iniciando...')

# Carrega variáveis globais
API_TOKEN: Final = os.getenv('BOT_TOKEN')
BOT_HANDLE: Final = os.getenv('BOT_NAME')
my_id: Final = os.getenv('ADMIN')

# Locks por usuário (id interno, não telegram_id) — evita que duas mensagens da MESMA pessoa
# mexam concorrentemente em `_histories[user_id]` (ia/agent.py) quando a chamada à LLM está
# rodando numa thread separada (ver process_message/reset_command).
_user_locks: dict[int, asyncio.Lock] = {}


def _lock_for(user_id: int) -> asyncio.Lock:
    return _user_locks.setdefault(user_id, asyncio.Lock())


# ==========================================
# 🛡️ DECORADOR DE SEGURANÇA
# ==========================================
def require_registration(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        tg_user = update.effective_user

        if not tg_user or tg_user.is_bot:
            return  # Ignora mensagens vazias ou de outros bots

        with get_user_service() as user_service:
            registered_user = user_service.is_registered(tg_user.id)
            has_access = registered_user and user_service.has_access(tg_user.id)

        # Verifica no banco se o usuário é válido
        if not registered_user:
            if update.message:
                await update.message.reply_text(
                    "Acesso negado! Se reistre primeiro. Use /register primeiro.")
            return  # Interrompe a função aqui. O usuário não faz mais nada.

        # Registrado, mas ainda sem liberação de acesso (free_access = False por padrão —
        # liberado manualmente no banco, ver README).
        if not has_access:
            if update.message:
                await update.message.reply_text(
                    "Cadastro recebido — aguarde a liberação de acesso.")
            return

        # Se ele for válido, deixa a função original rodar
        return await func(update, context, *args, **kwargs)

    return wrapper


# ==========================================
# COMANDOS DO BOT
# ==========================================

# O /register NÃO leva a tag @require_registration, pois a pessoa precisa dele para entrar
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user

    with get_user_service() as user_service:
        if user_service.is_registered(tg_user.id):
            await update.message.reply_text(f"Olá {tg_user.full_name}, você já está registrado!")
        else:
            user = UserCreateDTO(
                telegram_id=tg_user.id,
                name=tg_user.name
            )
            user_service.create(user)
            await update.message.reply_text(
                f"Olá {tg_user.full_name}, você foi registrado! Aguarde a liberação de acesso.")

# Daqui pra baixo, TUDO exige registro. Basta colocar o @require_registration em cima da função!

@require_registration
async def initiate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Fala meu chegado, como vai?')


@require_registration
async def assist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Here comes the help')


@require_registration
async def personalize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command, you can put whatever you want here.')


@require_registration
async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Sim mestre, estou funcionando perfeitamente')


@require_registration
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # reset_chat/chat() são indexados pelo id INTERNO do usuário, não o telegram_id — resolver
    # aqui do mesmo jeito que process_message, senão o reset nunca atinge o histórico certo.
    with get_user_service() as user_service:
        user = user_service.find_by_telegram_id(update.effective_user.id)

    async with _lock_for(user.id):
        await asyncio.to_thread(llm_service.reset_chat, user.id)
    await update.message.reply_text("Memória resetada. Cuidado.")


@require_registration
async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    chat_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({tg_user.id}) in {chat_type}: "{text}"')

    # Trata mensagens em grupo (só responde se o bot for mencionado)
    if chat_type in ['group', 'supergroup']:
        if BOT_HANDLE not in text:
            return
        text = text.replace(BOT_HANDLE, '').strip()
    with get_user_service() as user_service:
        user = user_service.find_by_telegram_id(tg_user.id)
        user_id = user.id

    # Como a função tem o @require_registration, se o código chegou nessa linha
    # nós temos certeza absoluta que o usuário é validado!
    # A chamada à LLM é bloqueante (requests.post em ia/client.py) e pode levar minutos num
    # cold-start do Ollama — asyncio.to_thread joga isso pra uma thread, liberando o event loop
    # pra atender outros usuários nesse meio-tempo (ver concurrent_updates no __main__). O lock
    # por usuário serializa só as mensagens da MESMA pessoa, protegendo _histories[user_id].
    async with _lock_for(user_id):
        response = await asyncio.to_thread(llm_service.chat, user_id, text)
    await update.message.reply_text(response)


# Log de erros
async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Erro gerado pelo update {update}: {context.error}')


# ==========================================
# INICIALIZAÇÃO DO BOT
# ==========================================
if __name__ == '__main__':
    # concurrent_updates: sem ele, o PTB processa um update por vez numa única corrotina
    # sequencial — mesmo com asyncio.to_thread nos handlers, não haveria nenhuma outra tarefa
    # agendada pra rodar enquanto uma chamada à LLM está em andamento. Sem limite fixo: o
    # require_registration já restringe quem gera tráfego, e o volume é pessoal/baixo.
    app = Application.builder().token(API_TOKEN).concurrent_updates(True).build()

    # Registra todos os comandos sem restrição na hora do start
    # O bloqueio agora ocorre quando o usuário manda a mensagem!
    app.add_handler(CommandHandler('start', initiate_command))
    app.add_handler(CommandHandler('help', assist_command))
    app.add_handler(CommandHandler('custom', personalize_command))
    app.add_handler(CommandHandler('teste', teste))
    app.add_handler(CommandHandler('register', register_command))
    app.add_handler(CommandHandler('reset', reset_command))

    app.add_handler(MessageHandler(filters.TEXT, process_message))
    app.add_error_handler(log_error)

    print('Starting polling...')
    app.run_polling(poll_interval=2)