from typing import Final
from pathlib import Path
from dotenv import load_dotenv
import os
import services.user_service
from core.database import init_db
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import services.expense_service
import services.gemini_service as gemini_service
from functools import wraps  # Importante: Biblioteca nativa do Python para criar o decorador

env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)
init_db()
print('O bot está iniciando...')

# Carrega variáveis globais
API_TOKEN: Final = os.getenv('BOT_TOKEN')
BOT_HANDLE: Final = os.getenv('BOT_NAME')
my_id: Final = os.getenv('ADMIN')
user_service: Final = services.user_service

init_db()

# ==========================================
# 🛡️ DECORADOR DE SEGURANÇA
# ==========================================
def require_registration(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        tg_user = update.effective_user

        if not tg_user or tg_user.is_bot:
            return  # Ignora mensagens vazias ou de outros bots

        # Verifica no banco se o usuário é válido
        if not user_service.is_verified(tg_user.id):
            if update.message:
                await update.message.reply_text(
                    "Acesso negado! Se reistre primeiro. Use /register primeiro.")
            return  # Interrompe a função aqui. O usuário não faz mais nada.

        # Se ele for válido, deixa a função original rodar
        return await func(update, context, *args, **kwargs)

    return wrapper


# ==========================================
# COMANDOS DO BOT
# ==========================================

# O /register NÃO leva a tag @require_registration, pois a pessoa precisa dele para entrar
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    id = tg_user.id
    is_verified = user_service.is_verified(id)

    if is_verified:
        await update.message.reply_text(f"Olá {tg_user.full_name}, você já está registrado!")
    else:
        user_service.register_user(id, tg_user.full_name)
        await update.message.reply_text(f"Olá {tg_user.full_name}, você foi registrado!")


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
    gemini_service.reset_chat(update.effective_user.id)
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

    # Como a função tem o @require_registration, se o código chegou nessa linha
    # nós temos certeza absoluta que o usuário é validado!
    response = gemini_service.chat(tg_user.id, text)
    await update.message.reply_text(response)


# Log de erros
async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Erro gerado pelo update {update}: {context.error}')


# ==========================================
# INICIALIZAÇÃO DO BOT
# ==========================================
if __name__ == '__main__':
    app = Application.builder().token(API_TOKEN).build()

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