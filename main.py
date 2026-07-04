import logging
from telegram.ext import Application
import config
from database import db
from handlers.admin import setup_admin_handlers
from handlers.test import setup_test_handlers
from handlers.user import setup_user_handlers

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("XATOLIK: config.py faylida BOT_TOKEN kiritilmagan yoki noto'g'ri!")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Setup handlers
    setup_admin_handlers(application)
    setup_test_handlers(application)
    setup_user_handlers(application)

    # Run the bot until the user presses Ctrl-C
    print("Bot ishga tushdi...")
    application.run_polling()

if __name__ == '__main__':
    main()
