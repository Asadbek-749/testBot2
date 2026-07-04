import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    PollAnswerHandler,
    ContextTypes
)
import config
from database import db
from utils.certificate import generate_certificate
from utils.helpers import check_admin

@check_admin
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await query.answer()
    
    if not query.data.startswith("topic_"):
        return
        
    topic = query.data.split("topic_")[1]
    chat_id = update.effective_chat.id
    # Forum topic id (message_thread_id)
    thread_id = update.effective_message.message_thread_id
    
    await query.edit_message_text(f"Tanlangan mavzu: {topic}. Test tayyorlanmoqda...")
    
    # Run test immediately as a background task
    asyncio.create_task(run_test_sequence(context.bot, chat_id, thread_id, topic, context.job_queue))

async def run_test_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data
    chat_id = data['chat_id']
    thread_id = data['thread_id']
    topic = data['topic']
    
    await run_test_sequence(context.bot, chat_id, thread_id, topic, context.job_queue)

async def run_test_sequence(bot, chat_id, thread_id, topic, job_queue):
    questions = db.get_questions_by_topic(topic)
    if not questions:
        await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=f"'{topic}' mavzusida savollar topilmadi.")
        return
        
    random.shuffle(questions)
    
    await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=f"🎉 Test boshlandi! Mavzu: {topic}\nJami savollar: {len(questions)}")
    
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
        
        await asyncio.sleep(20)
    
    await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text="Natijalar hisoblanmoqda...")
    await asyncio.sleep(2) # Give a little time for final answers to process
    
    results = db.get_test_results(poll_ids)
    
    # Save results to db
    db.save_final_results(results, topic)
    
    if not results:
        await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text="Hozirgi testda hech kim to'g'ri javob topmadi.")
    else:
        top3 = results[:3]
        text = "🏆 Top 3 ishtirokchilar:\n\n"
        for i, res in enumerate(top3):
            text += f"{i+1}. {res['name']} - {res['score']} ta to'g'ri\n"
        
        await bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=text)
        
        # Sertifikat uchun (faqat 1-o'rin 0 dan katta ball olsa)
        first_place = top3[0]
        if first_place['score'] > 0:
            cert_path = generate_certificate(first_place['name'], topic, first_place['score'])
            with open(cert_path, 'rb') as cert_file:
                await bot.send_photo(
                    chat_id=chat_id,
                    message_thread_id=thread_id,
                    photo=cert_file,
                    caption=f"🎉 Tabriklaymiz, {first_place['name']}! Siz 1-o'rinni egalladingiz!"
                )
    
    # 2 daqiqadan so'ng pollarni o'chirish uchun JobQueue
    job_queue.run_once(
        delete_polls_job,
        120,
        data={'chat_id': chat_id, 'message_ids': poll_message_ids}
    )

async def delete_polls_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data['chat_id']
    message_ids = job.data['message_ids']
    
    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            print(f"Xatolik: {e}")

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
    application.add_handler(CallbackQueryHandler(topic_callback, pattern="^topic_"))
    application.add_handler(PollAnswerHandler(handle_poll_answer))
