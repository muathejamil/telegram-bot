from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command and display the main menu"""
    keyboard = [
        [InlineKeyboardButton("", callback_data='start')],
        [InlineKeyboardButton(" 👨‍💼الملف الشخصي", callback_data='generateid')],
        [InlineKeyboardButton(" 💸إيداع USDT", callback_data='depositusdt')],
        [InlineKeyboardButton(" 🚒قائمة البطاقات", callback_data='cardlist')],
        [InlineKeyboardButton(" 🤔طريقة استخدام البوت", callback_data='howtouse')],
        [InlineKeyboardButton("💳شروط استبدال البطاقه", callback_data='cardreplaceinstructions')],
        [InlineKeyboardButton(" ❌القائمه السوداء", callback_data='blacklist')]
    ]
    user = update.effective_user
    print(user)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('مرحبًا! اختر خيارًا من القائمة:', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks from the inline keyboard"""
    query = update.callback_query
    await query.answer()
    
    # Handle different menu options
    if query.data == 'start':
        await query.edit_message_text(text="مرحبًا! تم بدء البوت وعرض القائمة.")
    elif query.data == 'generateid':
        await query.edit_message_text(text="سيتم إنشاء معرف البطاقة الخاص بك قريبًا.")
    elif query.data == 'depositusdt':
        await query.edit_message_text(text="لإيداع USDT في حساب البوت، يرجى اتباع التعليمات التالية...")
    elif query.data == 'cardlist':
       await  query.edit_message_text(text="قائمة البطاقات المتاحة:")
    elif query.data == 'howtouse':
        await query.edit_message_text(text="كيفية استخدام البوت:\n1. اختر الخيار المطلوب\n2. اتبع التعليمات\n3. استمتع بالخدمة")
    elif query.data == 'cardreplaceinstructions':
        await query.edit_message_text(text="تعليمات استبدال البطاقة:\n- تأكد من صحة البيانات\n- اتبع الخطوات بدقة")
    elif query.data == 'blacklist':
        await query.edit_message_text(text="القائمة السوداء - المستخدمين المحظورين")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")

def main() -> None:
    """Main function to start the bot"""
    # Your bot token
    TOKEN = "7857065897:AAGM-nDNhZ8DDaTFGTt3g4CDlHXb355K5ps"
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()