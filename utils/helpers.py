from telegram import Update
from telegram.ext import ContextTypes
import config

def check_admin(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in config.ADMIN_IDS:
            return
        return await func(update, context)
    return wrapper
