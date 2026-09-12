import os
import openpyxl
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
import config
from database import db
from utils.helpers import check_admin

@check_admin
async def add_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This was a conversation handler in earlier versions, but we can just use the simple version or keep it simple.
    # To save space and time, the user uses Excel mostly. Let's restore the excel handler.
    await update.message.reply_text("Savol qo'shish uchun Excel fayl yuboring.")

@check_admin
async def list_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = db.get_all_questions()
    if not questions:
        await update.message.reply_text("Bazada savollar yo'q.")
        return
        
    text = "Savollar ro'yxati:\n\n"
    for q in questions:
        text += f"ID: {q['id']} | Mavzu: {q['topic']} | Savol: {q['text'][:20]}...\n"
        
    await update.message.reply_text(text)

@check_admin
async def delete_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /delete_question <ID>")
        return
        
    try:
        q_id = int(context.args[0])
        db.delete_question(q_id)
        await update.message.reply_text(f"Savol (ID: {q_id}) o'chirildi.")
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
        f"Qatnashgan foydalanuvchilar: {u_count}\n"
        f"Yechilgan testlar: {r_count}"
    )
    await update.message.reply_text(text)

@check_admin
async def handle_excel_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith('.xlsx'):
        await update.message.reply_text("Iltimos, faqat .xlsx formatidagi Excel fayl yuboring.")
        return
        
    file = await context.bot.get_file(doc.file_id)
    file_path = os.path.join(os.path.dirname(__file__), "..", "temp.xlsx")
    await file.download_to_drive(file_path)
    
    try:
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        
        count = 0
        # Format: Savol, Opt1, Opt2, Opt3, Correct(1-3), Topic
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]: continue
            
            try:
                question = str(row[0])
                opt1 = str(row[1])
                opt2 = str(row[2])
                opt3 = str(row[3])
                correct_id = int(row[4])
                topic = str(row[5])
                
                if correct_id not in [1, 2, 3]:
                    raise ValueError("To'g'ri javob raqami 1, 2 yoki 3 bo'lishi kerak.")
                    
                db.add_question(question, opt1, opt2, opt3, correct_id, topic)
                count += 1
            except Exception as e:
                await update.message.reply_text(f"Xatolik qatorda: {row}\nSabab: {e}")
                
        await update.message.reply_text(f"Muvaffaqiyatli {count} ta savol qo'shildi!")
    except Exception as e:
        await update.message.reply_text(f"Excel hujjatda xatolik: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def setup_admin_handlers(application):
    application.add_handler(CommandHandler("list_questions", list_questions))
    application.add_handler(CommandHandler("delete_question", delete_question))
    application.add_handler(CommandHandler("delete_all", delete_all_questions_command))
    application.add_handler(CommandHandler("delete_topic", delete_topic_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_excel_document))
