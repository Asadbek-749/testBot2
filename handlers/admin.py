import os
import io
import openpyxl
from datetime import datetime, time, timedelta
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
import config
from database import db
from .test import run_test_job
from utils.helpers import check_admin

# ConversationHandler states for /add_question
ASK_TEXT, ASK_OPTS, ASK_CORRECT, ASK_TOPIC = range(4)

@check_admin
async def add_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Yangi savol matnini kiriting:")
    return ASK_TEXT

async def add_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['q_text'] = update.message.text
    await update.message.reply_text("Endi 3 ta variantni vergul bilan ajratib kiriting (masalan: Olma, Anor, Nok):")
    return ASK_OPTS

async def add_question_opts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    opts = [o.strip() for o in update.message.text.split(',')]
    if len(opts) != 3:
        await update.message.reply_text("Iltimos, aynan 3 ta variantni vergul bilan ajratib kiriting:")
        return ASK_OPTS
    context.user_data['q_opts'] = opts
    await update.message.reply_text("To'g'ri javob raqamini kiriting (1, 2 yoki 3):")
    return ASK_CORRECT

async def add_question_correct(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        correct_id = int(update.message.text)
        if correct_id not in [1, 2, 3]:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Iltimos, 1, 2 yoki 3 raqamidan birini kiriting:")
        return ASK_CORRECT
    
    context.user_data['q_correct'] = correct_id
    await update.message.reply_text("Savol qaysi mavzuga tegishli? (Masalan: Matematika):")
    return ASK_TOPIC

async def add_question_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    topic = update.message.text
    q_text = context.user_data['q_text']
    opts = context.user_data['q_opts']
    correct_id = context.user_data['q_correct']
    
    db.add_question(q_text, opts[0], opts[1], opts[2], correct_id, topic)
    await update.message.reply_text("Savol muvaffaqiyatli bazaga qo'shildi!")
    context.user_data.clear()
    return ConversationHandler.END

async def add_question_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Savol qo'shish bekor qilindi.")
    context.user_data.clear()
    return ConversationHandler.END

@check_admin
async def list_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = db.get_all_questions()
    if not questions:
        await update.message.reply_text("Bazada savollar yo'q.")
        return
    
    text = "Savollar ro'yxati:\n\n"
    for q in questions:
        text += f"ID: {q['id']} | Mavzu: {q['topic']}\nSavol: {q['text']}\nJavoblar: 1){q['opt1']} 2){q['opt2']} 3){q['opt3']}\nTo'g'ri: {q['correct_id']}\n\n"
        if len(text) > 3500:
            await update.message.reply_text(text)
            text = ""
    
    if text:
        await update.message.reply_text(text)

@check_admin
async def delete_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /delete_question <id>")
        return
    try:
        q_id = int(context.args[0])
        db.delete_question(q_id)
        await update.message.reply_text(f"{q_id}-raqamli savol o'chirildi.")
    except ValueError:
        await update.message.reply_text("Noto'g'ri ID format.")

@check_admin
async def delete_all_questions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.delete_all_questions()
    await update.message.reply_text("Barcha savollar bazadan muvaffaqiyatli o'chirildi! Endi yangi Excel fayl yuklashingiz mumkin.")

@check_admin
async def delete_topic_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /delete_topic <mavzu_nomi>")
        return
    topic = " ".join(context.args)
    deleted_count = db.delete_topic(topic)
    
    if deleted_count > 0:
        await update.message.reply_text(f"'{topic}' mavzusi va uning barcha ({deleted_count} ta) savollari muvaffaqiyatli o'chirildi.")
    else:
        await update.message.reply_text(f"'{topic}' nomli mavzu topilmadi. Harflar katta-kichikligiga e'tibor bermasdan yozsangiz ham bo'ladi, lekin yozilishi aniq bo'lishi kerak (Masalan: MS Excel).")

@check_admin
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Iltimos, tarqatmoqchi bo'lgan xabaringizga 'Reply' qilib /broadcast deb yozing.")
        return
        
    targets = db.get_all_chats_and_users()
    if not targets:
        await update.message.reply_text("Hali bazada xabar yuborish uchun hech qanday foydalanuvchi yoki guruh yo'q.")
        return

    msg = update.message.reply_to_message
    success = 0
    await update.message.reply_text("Xabar tarqatish boshlandi, biroz kuting...")
    
    for t_id in targets:
        try:
            await msg.copy(chat_id=t_id)
            success += 1
        except Exception:
            pass
            
    await update.message.reply_text(f"Xabar {success} ta guruh va foydalanuvchiga muvaffaqiyatli yuborildi.")

@check_admin
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_count, u_count, r_count = db.get_stats()
    text = (
        f"📊 Bot Statistikasi:\n\n"
        f"Jami savollar: {q_count}\n"
        f"Jami noyob foydalanuvchilar: {u_count}\n"
        f"Jami yechilgan testlar (sessiyalar): {r_count}"
    )
    await update.message.reply_text(text)

@check_admin
async def handle_excel_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith('.xlsx'):
        return
    
    try:
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
        sheet = wb.active
        
        added_count = 0
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            
            # Savol, Opt1, Opt2, Opt3, Correct, Topic
            if len(row) < 6:
                raise ValueError("Noto'g'ri ustunlar soni")
                
            q_text = str(row[0])
            opt1 = str(row[1])
            opt2 = str(row[2])
            opt3 = str(row[3])
            try:
                correct_id = int(row[4])
                if correct_id not in [1, 2, 3]:
                    raise ValueError("To'g'ri javob raqami xato")
            except:
                raise ValueError("To'g'ri javob raqami xato")
            topic = str(row[5])
            
            db.add_question(q_text, opt1, opt2, opt3, correct_id, topic)
            added_count += 1
            
        await update.message.reply_text(f"Exceldan {added_count} ta savol muvaffaqiyatli qo'shildi!")
    except Exception as e:
        await update.message.reply_text("Excel hujjatda xatolik")

@check_admin
async def schedule_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /schedule_test <mavzu> <soat:daqiqa>
    if len(context.args) < 2:
        await update.message.reply_text("Foydalanish: /schedule_test <mavzu> <soat:daqiqa>")
        return
        
    time_str = context.args[-1]
    topic = " ".join(context.args[:-1])
    
    try:
        h, m = map(int, time_str.split(':'))
        target_time = time(hour=h, minute=m)
        
        # Calculate time difference
        now = datetime.now()
        target_datetime = now.replace(hour=h, minute=m, second=0, microsecond=0)
        
        if target_datetime < now:
            target_datetime += timedelta(days=1)
            
        seconds_diff = (target_datetime - now).total_seconds()
        
        chat_id = update.effective_chat.id
        thread_id = update.message.message_thread_id
        
        context.job_queue.run_once(
            run_test_job, 
            seconds_diff, 
            data={'chat_id': chat_id, 'thread_id': thread_id, 'topic': topic}
        )
        await update.message.reply_text(f"Test '{topic}' mavzusida {time_str} da (ya'ni {int(seconds_diff)} soniyadan so'ng) avtomatik boshlanadi.")
    except Exception as e:
        await update.message.reply_text("Vaqt formati xato. HH:MM ko'rinishida kiriting.")

add_question_handler = ConversationHandler(
    entry_points=[CommandHandler('add_question', add_question_start)],
    states={
        ASK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_text)],
        ASK_OPTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_opts)],
        ASK_CORRECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_correct)],
        ASK_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_topic)],
    },
    fallbacks=[CommandHandler('cancel', add_question_cancel)]
)

def setup_admin_handlers(application):
    application.add_handler(add_question_handler)
    application.add_handler(CommandHandler("list_questions", list_questions))
    application.add_handler(CommandHandler("delete_question", delete_question))
    application.add_handler(CommandHandler("delete_all", delete_all_questions_command))
    application.add_handler(CommandHandler("delete_topic", delete_topic_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("schedule_test", schedule_test_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_excel_document))
