from typing import Final
from pathlib import Path
from dotenv import load_dotenv
import os
import services.user_service
from core.database import init_db

init_db()

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
print('O bot esta iniciando...')

# Encontra o arquivo .env na raiz do projeto
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

API_TOKEN: Final = os.getenv('BOT_TOKEN')
BOT_HANDLE: Final = os.getenv('BOT_NAME')
my_id: Final = os.getenv('ADMIN')
user_service: Final = services.user_service

# Command to start the bot
async def initiate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Fala meu chegado, como vai?')


# Command to provide help information
async def assist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Here comes the help')


# Command for custom functionality
async def personalize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This is a custom command, you can put whatever you want here.')

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Sim mestre, estou funcionando perfeitamente')

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    id = tg_user.id
    is_registered = user_service.get_name(id)
    user = user_service.get_name(id)
    # Chama o backend de forma simples
    if(is_registered):
        await update.message.reply_text(f"Olá {user}, você ja está registrado!")
    else:
        user_service.register_user(id, tg_user.full_name)
        await update.message.reply_text(f"Olá {user}, você foi registrado!")

def generate_response(id: int, username: str, user_input: str) -> str:
    # Custom logic for response generation
    normalized_input: str = user_input.lower()

    if 'hi' in normalized_input:
        is_admin = id == int(my_id)
        if is_admin:
            return f'Olá {username}, meu lindo gostoso!'
        else:

            return f'Olá {username}!'

    if 'how are you doing' in normalized_input:
        return 'I am functioning properly!'

    if 'i would like to subscribe' in normalized_input:
        return 'Sure go ahead!'

    return 'I didn’t catch that, could you please rephrase?'


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    # Extract details of the incoming message
    chat_type: str = update.message.chat.type
    text: str = update.message.text
    username = user_service.get_name(tg_user.id)
    # Logging for troubleshooting
    print(f'User ({update.message.chat.id}) in {chat_type}: "{text}"')

    # Handle group messages only if bot is mentioned
    if chat_type == 'group':
        if BOT_HANDLE in text:
            cleaned_text: str = text.replace(BOT_HANDLE, '').strip()
            response: str = generate_response(cleaned_text)
        else:
            return  # Ignore messages where bot is not mentioned in a group
    else:
        response: str = generate_response(tg_user.id, username, text)

    # Reply to the user
    print('Bot response:', response)
    await update.message.reply_text(response)


# Log errors
async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


# Start the bot
if __name__ == '__main__':
    app = Application.builder().token(API_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler('start', initiate_command))
    app.add_handler(CommandHandler('help', assist_command))
    app.add_handler(CommandHandler('custom', personalize_command))
    app.add_handler(CommandHandler('teste', teste))
    app.add_handler(CommandHandler('register', register_command))

    # Register message handler
    app.add_handler(MessageHandler(filters.TEXT, process_message))

    # Register error handler
    app.add_error_handler(log_error)

    print('Starting polling...')
    # Run the bot
    app.run_polling(poll_interval=2)