from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from database import db
import config

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    text = "🤖 *Asadbek Code Club Test Boti*\n\n"
    text += "👥 *Foydalanuvchi buyruqlari:*\n"
    text += "📊 /mystats - O'zingizning natijalaringizni ko'rish\n"
    text += "🏆 /rating - Mavzular bo'yicha kuchlilar reytingini ko'rish\n\n"
    
    if user_id in config.ADMIN_IDS:
        text += "👑 *Admin buyruqlari:*\n"
        text += "🎮 /test - Guruhda test boshlash\n"
        text += "➕ /add_question - Bitta yangi savol qo'shish\n"
        text += "📝 /list_questions - Barcha savollarni ko'rish\n"
        text += "🗑 /delete_question <ID> - Bitta savolni o'chirish\n"
        text += "🧹 /delete_topic <Mavzu> - Bitta mavzuni barcha savollari bilan o'chirish\n"
        text += "🧨 /delete_all - Barcha savollarni butunlay tozalash\n"
        text += "📊 /stats - Bot va o'yin statistikasini ko'rish\n"
        text += "🕒 /schedule_test <Mavzu> <HH:MM> - Testni aniq vaqtga rejalashtirish\n"
        text += "📢 /broadcast - Barchaga xabar tarqatish (e'lon xabariga Reply qilib yoziladi)\n\n"
        text += "📁 Yoki Excel (.xlsx) faylni botga shunchaki tashlash orqali savollarni yuztalab ommaviy qo'shishingiz mumkin."

    await update.message.reply_text(text, parse_mode='Markdown')

async def mystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = db.get_user_stats(user_id)
    
    if not stats:
        await update.message.reply_text("Siz hali hech qanday testda qatnashmagansiz.")
        return
        
    text = "👤 Sizning statistikangiz:\n\n"
    for s in stats:
        text += f"Mavzu: {s['topic']} | Eng yuqori ball: {s['max_score']} | Urinishlar: {s['attempts']}\n"
        
    await update.message.reply_text(text)

async def rating_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topics = db.get_topics()
    if not topics:
        await update.message.reply_text("Bazada ma'lumot yo'q.")
        return
        
    keyboard = []
    for topic in topics:
        keyboard.append([InlineKeyboardButton(topic, callback_data=f"rating_{topic}")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Qaysi mavzu bo'yicha reytingni ko'rmoqchisiz?", reply_markup=reply_markup)

async def rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("rating_"):
        return
        
    topic = query.data.split("rating_")[1]
    rating_data = db.get_group_rating(topic)
    
    if not rating_data:
        await query.edit_message_text(f"'{topic}' mavzusi bo'yicha reyting yo'q.")
        return
        
    text = f"🏆 '{topic}' mavzusi bo'yicha Top 10:\n\n"
    for i, r in enumerate(rating_data):
        text += f"{i+1}. {r['name']} - {r['max_score']} ball\n"
        
    await query.edit_message_text(text)

def setup_user_handlers(application):
    application.add_handler(CommandHandler("start", help_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mystats", mystats_command))
    application.add_handler(CommandHandler("rating", rating_command))
    application.add_handler(CallbackQueryHandler(rating_callback, pattern="^rating_"))
