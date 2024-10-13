import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers import start, join_game_callback, set_key_callback, play_card_callback

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No token found! Set the BOT_TOKEN environment variable.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(join_game_callback, pattern="^join_game$"))
    application.add_handler(CallbackQueryHandler(set_key_callback, pattern="^set_key_"))
    application.add_handler(CallbackQueryHandler(play_card_callback, pattern="^play_"))

    application.run_polling()

if __name__ == "__main__":
    main()