import os

admin_code = """import os
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
        
    text = "Savollar ro'yxati:\\n\\n"
    for q in questions:
        text += f"ID: {q['id']} | Mavzu: {q['topic']} | Savol: {q['text'][:20]}...\\n"
        
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
        f"📊 Bot Statistikasi:\\n\\n"
        f"Jami savollar: {q_count}\\n"
        f"Qatnashgan foydalanuvchilar: {u_count}\\n"
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
                await update.message.reply_text(f"Xatolik qatorda: {row}\\nSabab: {e}")
                
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
"""

with open('handlers/admin.py', 'w', encoding='utf-8') as f:
    f.write(admin_code)

test_code = """import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, PollAnswerHandler, ContextTypes
import config
from database import db
from utils.certificate import generate_certificate
from utils.helpers import check_admin

active_tests = {}

@check_admin
async def stop_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_tests and active_tests[chat_id]:
        active_tests[chat_id] = False
        await update.message.reply_text("🛑 Test darhol to'xtatildi!")
    else:
        await update.message.reply_text("Bu guruhda hozir hech qanday test bo'layotgani yo'q.")

@check_admin
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if active_tests.get(chat_id, False):
        await update.message.reply_text("Bu guruhda allaqachon bitta test davom etmoqda. Avval uni tugatishini kuting yoki /stop_test orqali to'xtating.")
        return

    topics = db.get_topics()
    if not topics:
        await update.message.reply_text("Bazada savollar yo'q.")
        return
        
    keyboard = []
    for topic in topics:
        keyboard.append([InlineKeyboardButton(topic, callback_data=f"topic_{topic}")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Test uchun mavzuni tanlang:", reply_markup=reply_markup)

async def topic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if update.effective_user.id not in config.ADMIN_IDS:
        await query.answer("Bu tugmani faqat admin bosa oladi!", show_alert=True)
        return
    
    chat_id = update.effective_chat.id
    if active_tests.get(chat_id, False):
        await query.answer("Bu guruhda allaqachon test ketyapti!", show_alert=True)
        return
        
    await query.answer()
    
    if not query.data.startswith("topic_"):
        return
        
    topic = query.data.split("topic_")[1]
    thread_id = update.effective_message.message_thread_id
    
    await query.edit_message_text(f"Tanlangan mavzu: {topic}. Test tayyorlanmoqda...")
    
    # Register test as active for this chat
    active_tests[chat_id] = True
    
    # Run test immediately as a background task
    asyncio.create_task(run_test_sequence(context.bot, chat_id, thread_id, topic, context.job_queue))

async def run_test_sequence(bot, chat_id, thread_id, topic, job_queue):
    questions = db.get_questions_by_topic(topic)
    if not questions:
        await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=f"'{topic}' mavzusida savollar topilmadi.")
        active_tests[chat_id] = False
        return
        
    random.shuffle(questions)
    
    await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=f"🎉 Test boshlandi! Mavzu: {topic}\\nJami savollar: {len(questions)}")
    
    poll_message_ids = []
    poll_ids = []
    
    for q in questions:
        options = [q['opt1'], q['opt2'], q['opt3']]
        correct_option_id = q['correct_id'] - 1
        
        message = await bot.send_poll(
            chat_id=chat_id,
            message_thread_id=thread_id,
            question=q['text'],
            options=options,
            type='quiz',
            correct_option_id=correct_option_id,
            is_anonymous=False,
            open_period=20
        )
        
        poll_id = message.poll.id
        poll_ids.append(poll_id)
        poll_message_ids.append(message.message_id)
        
        # Save active poll for tracking
        db.add_active_poll(poll_id, chat_id, correct_option_id)
        
        # Checking roughly every second to respond quickly to /stop_test
        for _ in range(20):
            if not active_tests.get(chat_id, False):
                break
            await asyncio.sleep(1)
            
        if not active_tests.get(chat_id, False):
            await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text="⚠️ Test admin tomonidan majburiy to'xtatildi! Savollar o'chirilmoqda...")
            job_queue.run_once(delete_polls_job, 1, data={'chat_id': chat_id, 'message_ids': poll_message_ids})
            return
    
    # Final check before results
    if not active_tests.get(chat_id, False):
        return
        
    await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text="Natijalar hisoblanmoqda...")
    await asyncio.sleep(2) # Give a little time for final answers to process
    
    results = db.get_test_results(poll_ids)
    
    # Save results to db
    db.save_final_results(results, topic)
    
    if not results:
        await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text="Hozirgi testda hech kim to'g'ri javob topmadi.")
    else:
        top3 = results[:3]
        text = "🏆 Top 3 ishtirokchilar:\\n\\n"
        for i, res in enumerate(top3):
            text += f"{i+1}. {res['name']} - {res['score']} ta to'g'ri\\n"
        
        await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=text)
        
        # Sertifikat uchun (faqat 1-o'rin 0 dan katta ball olsa)
        first_place = top3[0]
        if first_place['score'] > 0:
            cert_id = db.issue_certificate(first_place['user_id'], first_place['name'], topic)
            cert_path = generate_certificate(first_place['name'], topic, first_place['score'], cert_id)
            with open(cert_path, 'rb') as cert_file:
                await bot.send_photo(
                    chat_id=chat_id,
                    message_thread_id=thread_id,
                    photo=cert_file,
                    caption=f"🎉 Tabriklaymiz, {first_place['name']}! Siz 1-o'rinni egalladingiz!\\nSertifikat ID: #{cert_id}"
                )
    
    # 2 daqiqadan so'ng pollarni o'chirish uchun JobQueue
    job_queue.run_once(
        delete_polls_job,
        120,
        data={'chat_id': chat_id, 'message_ids': poll_message_ids}
    )
    
    # Mark test as finished
    active_tests[chat_id] = False

async def delete_polls_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data['chat_id']
    message_ids = job.data['message_ids']
    
    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    poll_id = answer.poll_id
    user_id = answer.user.id
    user_name = answer.user.first_name
    
    # Check if this poll is in our active test
    active_poll = db.get_active_poll(poll_id)
    if active_poll:
        correct_option_id = active_poll['correct_option_id']
        is_correct = answer.option_ids and answer.option_ids[0] == correct_option_id
        
        db.add_poll_answer(poll_id, user_id, user_name, is_correct)

def setup_test_handlers(application):
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("stop_test", stop_test_command))
    application.add_handler(CallbackQueryHandler(topic_callback, pattern="^topic_"))
    application.add_handler(PollAnswerHandler(handle_poll_answer))
"""

with open('handlers/test.py', 'w', encoding='utf-8') as f:
    f.write(test_code)

user_code = """from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from database import db
import config

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    text = "🤖 *Asadbek Code Club Test Boti*\\n\\n"
    text += "👥 *Foydalanuvchi buyruqlari:*\\n"
    text += "📊 /mystats - O'zingizning natijalaringizni ko'rish\\n"
    text += "🏆 /rating - Mavzular bo'yicha kuchlilar reytingini ko'rish\\n\\n"
    
    if user_id in config.ADMIN_IDS:
        text += "👑 *Admin buyruqlari:*\\n"
        text += "🎮 /test - Guruhda test boshlash\\n"
        text += "🛑 /stop_test - Davom etayotgan testni to'xtatish\\n"
        text += "📝 /list_questions - Barcha savollarni ko'rish\\n"
        text += "🗑 /delete_question <ID> - Bitta savolni o'chirish\\n"
        text += "🧹 /delete_topic <Mavzu> - Bitta mavzuni barcha savollari bilan o'chirish\\n"
        text += "🧨 /delete_all - Barcha savollarni butunlay tozalash\\n"
        text += "📊 /stats - Bot va o'yin statistikasini ko'rish\\n"
        text += "📢 /broadcast - Barchaga xabar tarqatish (e'lon xabariga Reply qilib yoziladi)\\n\\n"
        text += "📁 Yoki Excel (.xlsx) faylni botga shunchaki tashlash orqali savollarni yuztalab ommaviy qo'shishingiz mumkin."

    await update.message.reply_text(text, parse_mode='Markdown')

async def mystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = db.get_user_stats(user_id)
    
    if not stats:
        await update.message.reply_text("Siz hali hech qanday testda qatnashmagansiz.")
        return
        
    text = "👤 Sizning statistikangiz:\\n\\n"
    for s in stats:
        text += f"Mavzu: {s['topic']} | Eng yuqori ball: {s['max_score']} | Urinishlar: {s['attempts']}\\n"
        
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
        
    text = f"🏆 '{topic}' mavzusi bo'yicha Top 10:\\n\\n"
    for i, r in enumerate(rating_data):
        text += f"{i+1}. {r['name']} - {r['max_score']} ball\\n"
        
    await query.edit_message_text(text)

def setup_user_handlers(application):
    application.add_handler(CommandHandler("start", help_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mystats", mystats_command))
    application.add_handler(CommandHandler("rating", rating_command))
    application.add_handler(CallbackQueryHandler(rating_callback, pattern="^rating_"))
"""

with open('handlers/user.py', 'w', encoding='utf-8') as f:
    f.write(user_code)

cert_code = """import os
import unicodedata
from PIL import Image, ImageDraw, ImageFont
import datetime

def normalize_text(text):
    # Normalize special unicode characters (like Math Alphanumerics) to standard Latin
    return unicodedata.normalize('NFKD', text)

def generate_certificate(name, topic, score, cert_id):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(base_dir, "template.jpg")
    name = normalize_text(name)
    output_path = os.path.join(base_dir, f"cert_{name.replace(' ', '_')}.jpg")
    font_path = os.path.join(base_dir, "Roboto-Bold.ttf")
    
    if not os.path.exists(template_path):
        img = Image.new('RGB', (1024, 682), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 1004, 662], outline=(0, 0, 0), width=5)
    else:
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        
    try:
        font_name = ImageFont.truetype(font_path, 48)
        font_topic = ImageFont.truetype(font_path, 32)
        font_score = ImageFont.truetype(font_path, 32)
        font_date = ImageFont.truetype(font_path, 24)
        font_id = ImageFont.truetype(font_path, 18)
    except IOError:
        font_name = ImageFont.load_default()
        font_topic = ImageFont.load_default()
        font_score = ImageFont.load_default()
        font_date = ImageFont.load_default()
        font_id = ImageFont.load_default()

    img_w, img_h = img.size
    text_color = (13, 27, 42) # Deep navy blue
    gold_color = (212, 175, 55) # Metallic gold
    date_str = datetime.datetime.now().strftime("%d.%m.%Y")
    
    # Helper for centered text
    def draw_centered_text(y, text, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((img_w - w) / 2, y), text, fill=fill, font=font)

    # Placing text beautifully on the clean image layout
    draw_centered_text(img_h * 0.46, name, font_name, gold_color)
    draw_centered_text(img_h * 0.60, f"Mavzu: {topic}", font_topic, text_color)
    draw_centered_text(img_h * 0.68, f"Natija: {score} ta to'g'ri", font_score, text_color)
    draw_centered_text(img_h * 0.76, f"Sana: {date_str}", font_date, text_color)
    
    # ID at the bottom right corner
    draw.text((img_w - 150, img_h - 50), f"ID: #{cert_id:04d}", fill=gold_color, font=font_id)
    
    img.save(output_path)
    return output_path
"""

with open('utils/certificate.py', 'w', encoding='utf-8') as f:
    f.write(cert_code)
