import os
import logging
from datetime import datetime
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from database import db_manager


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command and display the main menu"""
    user = update.effective_user
    
    # Check if user is blacklisted
    if await db_manager.is_blacklisted(user.id):
        await update.message.reply_text('عذراً، لقد تم حظرك من استخدام هذا البوت.')
        return
    
    # Create user if doesn't exist
    await db_manager.create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث القائمة", callback_data='start')],
        [InlineKeyboardButton(" 👨‍💼الملف الشخصي", callback_data='generateid')],
        [InlineKeyboardButton(" 💸إيداع USDT", callback_data='depositusdt')],
        [InlineKeyboardButton(" 🚒قائمة البطاقات", callback_data='cardlist')],
        [InlineKeyboardButton(" 🤔طريقة استخدام البوت", callback_data='howtouse')],
        [InlineKeyboardButton("💳شروط استبدال البطاقه", callback_data='cardreplaceinstructions')],
        [InlineKeyboardButton(" ❌القائمه السوداء", callback_data='blacklist')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('مرحبًا! اختر خيارًا من القائمة:', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks from the inline keyboard"""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    
    # Check if user is blacklisted
    if await db_manager.is_blacklisted(user.id):
        await query.edit_message_text(text='عذراً، لقد تم حظرك من استخدام هذا البوت.')
        return
    
    # Handle different menu options
    if query.data == 'start':
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث القائمة", callback_data='start')],
            [InlineKeyboardButton(" 👨‍💼الملف الشخصي", callback_data='generateid')],
            [InlineKeyboardButton(" 💸إيداع USDT", callback_data='depositusdt')],
            [InlineKeyboardButton(" 🚒قائمة البطاقات", callback_data='cardlist')],
            [InlineKeyboardButton(" 🤔طريقة استخدام البوت", callback_data='howtouse')],
            [InlineKeyboardButton("💳شروط استبدال البطاقه", callback_data='cardreplaceinstructions')],
            [InlineKeyboardButton(" ❌القائمه السوداء", callback_data='blacklist')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="مرحبًا! اختر خيارًا من القائمة:", reply_markup=reply_markup)
        
    elif query.data == 'generateid':
        user_data = await db_manager.get_user(user.id)
        balance = user_data.get('balance', 0.0) if user_data else 0.0
        
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        profile_text = f"""
👨‍💼 الملف الشخصي

🆔 معرف المستخدم: {user.id}
👤 الاسم: {user.first_name or 'غير محدد'}
📧 اسم المستخدم: @{user.username or 'غير محدد'}
💰 الرصيد: ${balance:.2f}
📅 تاريخ التسجيل: {user_data.get('created_at', 'غير محدد') if user_data else 'غير محدد'}
        """
        await query.edit_message_text(text=profile_text, reply_markup=reply_markup)
        
    elif query.data == 'depositusdt':
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        deposit_text = f"""
💸 إيداع USDT

لإيداع USDT في حساب البوت، يرجى اتباع التعليمات التالية:

⚠️ تأكد من إرسال المعاملة من محفظة تدعم شبكة TRON (TRC20)

1️⃣ أرسل المبلغ المطلوب إيداعه إلى العنوان التالي:
📧 العنوان: {os.getenv('BINANCE_WALLET_TOKEN')}

ID BINANCE: {os.getenv('BINANCE_WALLET_ID')}

Binance gift card (بطاقة بايننس)
Itunes gift card (بطاقة إيتونس)

2️⃣ أرسل صورة من إيصال التحويل مع معرف المستخدم الخاص بك

3️⃣ انتظر التأكيد من الإدارة (عادة خلال 1 ساعة)
        """
        await query.edit_message_text(text=deposit_text, reply_markup=reply_markup)
        
    elif query.data == 'cardlist':
        # Show available countries
        countries = await db_manager.get_available_countries()
        
        if countries:
            keyboard = []
            for country in countries:
                keyboard.append([InlineKeyboardButton(
                    f"{country.get('flag', '🌍')} {country['name']}", 
                    callback_data=f"country_{country['code']}"
                )])
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text="🌍 اختر الدولة التي تريد شراء بطاقات لها:",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="😔 لا توجد دول متاحة حالياً",
                reply_markup=reply_markup
            )
        
    elif query.data == 'howtouse':
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        help_text = """
🤔 طريقة استخدام البوت

1️⃣ قم بإيداع USDT في حسابك ،ومشاركة وصل الدفع مع بوت الدعم
2️⃣ تصفح قائمة البطاقات المتاحة
3️⃣ اختر البطاقة المناسبة لك
4️⃣ تأكد من وجود رصيد كافي
5️⃣ اتبع التعليمات لإتمام الشراء
6️⃣ استلم تفاصيل البطاقة

💡 نصائح مهمة:
• تأكد من صحة البيانات قبل الشراء
• احتفظ بتفاصيل البطاقة في مكان آمن
• تواصل مع الدعم في حالة وجود مشاكل
        """
        await query.edit_message_text(text=help_text, reply_markup=reply_markup)
        
    elif query.data == 'cardreplaceinstructions':
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        replace_text = """
💳 شروط استبدال البطاقة

📋 الشروط العامة:
• يجب الإبلاغ عن المشكلة خلال 24 ساعة من الشراء
• تقديم دليل على عدم عمل البطاقة
• عدم استخدام البطاقة بشكل خاطئ

🔄 عملية الاستبدال:
1️⃣ تواصل مع الدعم الفني
2️⃣ قدم تفاصيل المشكلة
3️⃣ أرسل صورة من محاولة الاستخدام
4️⃣ انتظر المراجعة والموافقة

⏰ مدة المعالجة: 24-48 ساعة
        """
        await query.edit_message_text(text=replace_text, reply_markup=reply_markup)
        
    elif query.data == 'blacklist':
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        blacklist_text = """
❌ مواقع جاهزه للتفريغ

        """
        await query.edit_message_text(text=blacklist_text, reply_markup=reply_markup)
    
    # Handle country selection
    elif query.data.startswith('country_'):
        country_code = query.data.split('_')[1]
        cards = await db_manager.get_cards_by_country(country_code)
        
        if cards:
            keyboard = []
            for card in cards:
                card_text = f"{card['card_type']} بـ{card['price']} USDT"
                keyboard.append([InlineKeyboardButton(
                    card_text,
                    callback_data=f"card_{card['card_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة لقائمة الدول", callback_data='cardlist')])
            keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get country name for display
            countries = await db_manager.get_available_countries()
            country_name = next((c['name'] for c in countries if c['code'] == country_code), country_code)
            
            await query.edit_message_text(
                text=f"🏷️ البطاقات المتاحة في {country_name}:\n\nاختر البطاقة التي تريد شراءها:",
                reply_markup=reply_markup
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 العودة لقائمة الدول", callback_data='cardlist')],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="😔 لا توجد بطاقات متاحة لهذه الدولة حالياً",
                reply_markup=reply_markup
            )
    
    # Handle card selection
    elif query.data.startswith('card_'):
        card_id = query.data.split('_')[1]
        card = await db_manager.get_card(card_id)
        
        if card and card.get('is_available', False):
            # Check user balance
            user_balance = await db_manager.get_user_balance(user.id)
            
            if user_balance >= card['price']:
                keyboard = [
                    [InlineKeyboardButton("✅ نعم، أريد الشراء", callback_data=f"confirm_{card_id}")],
                    [InlineKeyboardButton("❌ لا، إلغاء", callback_data=f"country_{card['country_code']}")],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                confirmation_text = f"""
🛒 تأكيد الطلب

📋 تفاصيل البطاقة:
🏷️ النوع: {card['card_type']}
🌍 الدولة: {card.get('country_name', 'غير محدد')}
💰 السعر: {card['price']} USDT
💳 رصيدك الحالي: {user_balance:.2f} USDT

❓ هل أنت متأكد من أنك تريد شراء هذه البطاقة؟
                """
                
                await query.edit_message_text(text=confirmation_text, reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("💸 إيداع USDT", callback_data='depositusdt')],
                    [InlineKeyboardButton("🔙 العودة للبطاقات", callback_data=f"country_{card['country_code']}")],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                insufficient_text = f"""
⚠️ رصيد غير كافي

💰 سعر البطاقة: {card['price']} USDT
💳 رصيدك الحالي: {user_balance:.2f} USDT
📉 تحتاج إلى: {card['price'] - user_balance:.2f} USDT إضافية

يرجى إيداع المبلغ المطلوب أولاً.
                """
                
                await query.edit_message_text(text=insufficient_text, reply_markup=reply_markup)
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 العودة لقائمة الدول", callback_data='cardlist')],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="😔 رصيدك غير كافي",
                reply_markup=reply_markup
            )
    
    # Handle order confirmation
    elif query.data.startswith('confirm_'):
        card_id = query.data.split('_')[1]
        card = await db_manager.get_card(card_id)
        
        if card and card.get('is_available', False):
            # Check balance again
            user_balance = await db_manager.get_user_balance(user.id)
            
            if user_balance >= card['price']:
                # Create order
                order_id = await db_manager.create_order(
                    user_id=user.id,
                    card_id=card_id,
                    country_code=card['country_code'],
                    amount=card['price']
                )
                
                if order_id:
                    # Deduct balance
                    await db_manager.update_user_balance(user.id, -card['price'])
                    
                    # Reserve the card
                    await db_manager.reserve_card(card_id, user.id)
                    
                    # Create transaction record
                    await db_manager.create_transaction(
                        user_id=user.id,
                        transaction_type='card_purchase',
                        amount=card['price'],
                        description=f"شراء بطاقة {card['card_type']}"
                    )
                    
                    # Send notification to admin
                    await send_admin_notification(context, user, card, order_id)
                    
                    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    success_text = f"""
✅ تم إنشاء الطلب بنجاح!

🆔 رقم الطلب: {order_id}
🏷️ نوع البطاقة: {card['card_type']}
💰 المبلغ المدفوع: {card['price']} USDT

📨 تم إرسال إشعار للإدارة وسيتم إرسال تفاصيل البطاقة قريباً.

⏰ وقت التسليم المتوقع: 5-30 دقيقة
                    """
                    
                    await query.edit_message_text(text=success_text, reply_markup=reply_markup)
                else:
                    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        text="❌ حدث خطأ في إنشاء الطلب. يرجى المحاولة مرة أخرى.",
                        reply_markup=reply_markup
                    )
            else:
                keyboard = [
                    [InlineKeyboardButton("💸 إيداع USDT", callback_data='depositusdt')],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    text="⚠️ رصيدك غير كافي لإتمام هذا الطلب.",
                    reply_markup=reply_markup
                )
        else:
            keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="😔 هذه البطاقة لم تعد متاحة.",
                reply_markup=reply_markup
            )

async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, user, card, order_id):
    """Send notification to admin about new order"""
    try:
        admin_id = os.getenv('ADMIN_USER_ID')
        if not admin_id:
            logging.warning("ADMIN_USER_ID not set in environment variables")
            return
        
        admin_id = int(admin_id)
        
        notification_text = f"""
🔔 طلب جديد!

👤 معلومات المستخدم:
🆔 ID: {user.id}
👤 الاسم: {user.first_name or 'غير محدد'}
📧 اسم المستخدم: @{user.username or 'غير محدد'}

🛒 تفاصيل الطلب:
🆔 رقم الطلب: {order_id}
🏷️ نوع البطاقة: {card['card_type']}
🌍 الدولة: {card.get('country_name', 'غير محدد')}
💰 المبلغ: {card['price']} USDT

⏰ وقت الطلب: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

يرجى إرسال تفاصيل البطاقة للمستخدم.
        """
        
        await context.bot.send_message(
            chat_id=admin_id,
            text=notification_text
        )
        
    except Exception as e:
        logging.error(f"Error sending admin notification: {e}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("Use /start to test this bot.")

async def startup_database(application):
    """Initialize database connection"""
    try:
        await db_manager.connect()
        logging.info("Database connected successfully")
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        raise

async def shutdown_database(application):
    """Close database connection"""
    await db_manager.disconnect()
    logging.info("Database disconnected")

def main() -> None:
    """Main function to start the bot"""
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Get bot token from environment or use default
    TOKEN = os.getenv('BOT_TOKEN', "7857065897:AAGM-nDNhZ8DDaTFGTt3g4CDlHXb355K5ps")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add startup and shutdown handlers
    application.post_init = startup_database
    application.post_shutdown = shutdown_database
    
    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    logging.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()