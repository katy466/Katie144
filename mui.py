import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8470427152:AAGFuDNNKYcXSJmgM_KgO2hTI1XoAVtB8OI'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎮 Начать игру", "📊 Статистика"]
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        'Добро пожаловать в игру "Угадай слово"! Выберите действие:',
        reply_markup=reply_markup
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🎮 Начать игру":
        # Инлайн-клавиатура для выбора уровня
        keyboard = [
            [InlineKeyboardButton("🐢 Легкий", callback_data="level_easy")],
            [InlineKeyboardButton("🐇 Средний", callback_data="level_medium")],
            [InlineKeyboardButton("🚀 Сложный", callback_data="level_hard")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите уровень сложности:", reply_markup=reply_markup)
    
    elif text == "📊 Статистика":
        await update.message.reply_text("Ваша статистика:\nПобед:\nПоражений:")
    
    
async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "level_easy":
        await query.edit_message_text("Выбран легкий уровень! Удачи!")
    elif query.data == "level_medium":
        await query.edit_message_text("Выбран средний уровень! Будет интересно!")
    elif query.data == "level_hard":
        await query.edit_message_text("Выбран сложный уровень! Вы смельчак!")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    application.add_handler(CallbackQueryHandler(handle_inline_buttons))
    
    application.run_polling()

if __name__ == '__main__':
    main()
