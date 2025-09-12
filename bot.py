import os
import logging
import asyncio
import base64
import io
from datetime import datetime, UTC
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from database import db_manager
from telegram.error import BadRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def safe_edit_message(query, text, reply_markup=None, fallback_answer="تم التحديث ✅"):
    """Safely edit a message, handling BadRequest errors for identical content"""
    try:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    except BadRequest as e:
        if "message is not modified" in str(e).lower():
            # Message content is identical, just answer the callback
            await query.answer(fallback_answer)
        else:
            # Re-raise other BadRequest errors
            raise e
    except Exception as e:
        logging.error(f"Unexpected error editing message: {e}")
        await query.answer("حدث خطأ، يرجى المحاولة مرة أخرى")


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
    current_time = datetime.now().strftime('%H:%M')
    menu_text = f"مرحبًا! اختر خيارًا من القائمة:\n\n🕐 آخر تحديث: {current_time}"
    await update.message.reply_text(menu_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks from the inline keyboard"""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    
    # Check if user is blacklisted
    if await db_manager.is_blacklisted(user.id):
        await safe_edit_message(query, 'عذراً، لقد تم حظرك من استخدام هذا البوت.')
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
        
        # Add timestamp to make the refresh meaningful and avoid identical content error
        current_time = datetime.now().strftime('%H:%M')
        menu_text = f"مرحبًا! اختر خيارًا من القائمة:\n\n🕐 آخر تحديث: {current_time}"
        
        await safe_edit_message(query, menu_text, reply_markup, "تم تحديث القائمة ✅")
        
    elif query.data == 'generateid':
        user_data = await db_manager.get_user(user.id)
        balance = user_data.get('balance', 0.0) if user_data else 0.0
        
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        profile_text = f"""👨‍💼 الملف الشخصي

🆔 معرف المستخدم: {user.id}
👤 الاسم: {user.first_name or 'غير محدد'}
📧 اسم المستخدم: @{user.username or 'غير محدد'}
💰 الرصيد: ${balance:.2f}
📅 تاريخ التسجيل: {user_data.get('created_at', 'غير محدد') if user_data else 'غير محدد'}"""
        await safe_edit_message(query, profile_text, reply_markup)
        
    elif query.data == 'depositusdt':
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        deposit_text = f"""💸 إيداع USDT

لإيداع USDT في حساب البوت، يرجى اتباع التعليمات التالية:

⚠️ تأكد من إرسال المعاملة من محفظة تدعم شبكة TRON (TRC20)

1️⃣ أرسل المبلغ المطلوب إيداعه إلى العنوان التالي:
📧 العنوان: {os.getenv('BINANCE_WALLET_TOKEN')}

ID BINANCE: {os.getenv('BINANCE_WALLET_ID')}

Binance gift card (بطاقة بايننس)
Itunes gift card (بطاقة إيتونس)

2️⃣ أرسل صورة من إيصال التحويل مع معرف المستخدم الخاص بك

3️⃣ انتظر التأكيد من الإدارة (عادة خلال 1 ساعة)"""
        await safe_edit_message(query, deposit_text, reply_markup)
        
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
        
        help_text = """🤔 طريقة استخدام البوت

1️⃣ قم بإيداع USDT في حسابك ،ومشاركة وصل الدفع مع بوت الدعم
2️⃣ تصفح قائمة البطاقات المتاحة
3️⃣ اختر البطاقة المناسبة لك
4️⃣ تأكد من وجود رصيد كافي
5️⃣ اتبع التعليمات لإتمام الشراء
6️⃣ استلم تفاصيل البطاقة

💡 نصائح مهمة:
• تأكد من صحة البيانات قبل الشراء
• احتفظ بتفاصيل البطاقة في مكان آمن
• تواصل مع الدعم في حالة وجود مشاكل @FastCardChat"""
        await query.edit_message_text(text=help_text, reply_markup=reply_markup)
        
    elif query.data == 'cardreplaceinstructions':
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        replace_text = """💳 شروط استبدال البطاقة

📋 الشروط العامة:
• يجب الإبلاغ عن المشكلة خلال 24 ساعة من الشراء
• تقديم دليل على عدم عمل البطاقة
• عدم استخدام البطاقة بشكل خاطئ

🔄 عملية الاستبدال:
1️⃣ تواصل مع الدعم الفني @FastCardChat
2️⃣ قدم تفاصيل المشكلة
3️⃣ أرسل صورة من محاولة الاستخدام
4️⃣ انتظر المراجعة والموافقة

⏰ مدة المعالجة: 24-48 ساعة"""
        await query.edit_message_text(text=replace_text, reply_markup=reply_markup)
        
    elif query.data == 'blacklist':
        # Show available black websites for purchase
        websites = await db_manager.get_available_black_websites()
        
        if websites:
            keyboard = []
            for website in websites:
                keyboard.append([InlineKeyboardButton(
                    f"🌐 {website['name']} - ${website['price']}",
                    callback_data=f"buy_website_{website['website_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            websites_text = "🌐 المواقع السوداء المتاحة\n\nاختر موقعاً لشرائه:"
            await safe_edit_message(query, websites_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لا توجد مواقع متاحة حالياً", reply_markup)
    
    # Handle country selection
    elif query.data.startswith('country_'):
        country_code = query.data.split('_')[1]
        grouped_cards = await db_manager.get_grouped_cards_by_country(country_code)
        
        if grouped_cards:
            keyboard = []
            for card_group in grouped_cards:
                # Format: "Visa 20.0 ب USDT (5)"
                card_text = f"{card_group['card_type']} {card_group['price']} USDT ({card_group['count']})"
                # Use card_group format for callback data: cardgroup_countrycode_cardtype_price
                callback_data = f"cardgroup_{country_code}_{card_group['card_type'].replace(' ', '_')}_{card_group['price']}"
                keyboard.append([InlineKeyboardButton(
                    card_text,
                    callback_data=callback_data
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
    
    # Handle card group selection (new grouped display)
    elif query.data.startswith('cardgroup_'):
        # Parse callback data: cardgroup_countrycode_cardtype_price
        parts = query.data.split('_')
        country_code = parts[1]
        card_type = parts[2].replace('_', ' ')  # Convert back from underscore format
        price = float(parts[3])
        
        # Get one available card from this group
        card = await db_manager.get_available_card_from_group(country_code, card_type, price)
        
        if card and card.get('is_available', False):
            # Check user balance
            user_balance = await db_manager.get_user_balance(user.id)
            
            if user_balance >= card['price']:
                keyboard = [
                    [InlineKeyboardButton("✅ نعم، أريد الشراء", callback_data=f"confirm_{card['card_id']}")],
                    [InlineKeyboardButton("❌ لا، إلغاء", callback_data=f"country_{card['country_code']}")],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                confirmation_text = f"""🛒 تأكيد الطلب

📋 تفاصيل البطاقة:
🏷️ النوع: {card['card_type']}
🌍 الدولة: {card.get('country_name', 'غير محدد')}
💰 السعر: {card['price']} USDT
💳 رصيدك الحالي: {user_balance:.2f} USDT

❓ هل أنت متأكد من أنك تريد شراء هذه البطاقة؟"""
                
                await query.edit_message_text(text=confirmation_text, reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("💸 إيداع USDT", callback_data='depositusdt')],
                    [InlineKeyboardButton("🔙 العودة للبطاقات", callback_data=f"country_{card['country_code']}")],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                insufficient_text = f"""⚠️ رصيد غير كافي

💰 سعر البطاقة: {card['price']} USDT
💳 رصيدك الحالي: {user_balance:.2f} USDT
📉 تحتاج إلى: {card['price'] - user_balance:.2f} USDT إضافية

يرجى إيداع المبلغ المطلوب أولاً."""
                
                await query.edit_message_text(text=insufficient_text, reply_markup=reply_markup)
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 العودة لقائمة الدول", callback_data='cardlist')],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="😔 لا توجد بطاقات متاحة من هذا النوع حالياً",
                reply_markup=reply_markup
            )
    
    # Handle card selection (legacy - for individual card selection)
    elif query.data.startswith('card_'):
        logger.info(f"data: {query.data}")
        # Remove 'card_' prefix to get the full card_id
        card_id = query.data[5:]  # Remove 'card_' (5 characters)
        logger.info(f"card_id: {card_id}")
        card = await db_manager.get_card(card_id)
        logger.info(f"Card: {card}")
        if card and card.get('is_available', False):
            

            # Check user balance
            user_balance = await db_manager.get_user_balance(user.id)
            
            if user_balance > card['price']:
                keyboard = [
                    [InlineKeyboardButton("✅ نعم، أريد الشراء", callback_data=f"confirm_{card_id}")],
                    [InlineKeyboardButton("❌ لا، إلغاء", callback_data=f"country_{card['country_code']}")],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                confirmation_text = f"""🛒 تأكيد الطلب

📋 تفاصيل البطاقة:
🏷️ النوع: {card['card_type']}
🌍 الدولة: {card.get('country_name', 'غير محدد')}
💰 السعر: {card['price']} USDT
💳 رصيدك الحالي: {user_balance:.2f} USDT

❓ هل أنت متأكد من أنك تريد شراء هذه البطاقة؟"""
                
                await query.edit_message_text(text=confirmation_text, reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("💸 إيداع USDT", callback_data='depositusdt')],
                    [InlineKeyboardButton("🔙 العودة للبطاقات", callback_data=f"country_{card['country_code']}")],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                insufficient_text = f"""⚠️ رصيد غير كافي

💰 سعر البطاقة: {card['price']} USDT
💳 رصيدك الحالي: {user_balance:.2f} USDT
📉 تحتاج إلى: {card['price'] - user_balance:.2f} USDT إضافية

يرجى إيداع المبلغ المطلوب أولاً."""
                
                await query.edit_message_text(text=insufficient_text, reply_markup=reply_markup)
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 العودة لقائمة الدول", callback_data='cardlist')],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="😔 لا توجد بطاقات متاحة حالياً",
                reply_markup=reply_markup
            )
    
    # Handle website purchase confirmation (must come before general confirm_ handler)
    elif query.data.startswith('confirm_buy_website_'):
        website_id = query.data[20:]  # Remove 'confirm_buy_website_' prefix
        website = await db_manager.get_black_website(website_id)
        
        if website:
            user_balance = await db_manager.get_user_balance(user.id)
            
            if user_balance >= website['price']:
                # Process the purchase
                success = await db_manager.purchase_black_website(website_id, user.id)
                
                if success:
                    # Deduct balance
                    await db_manager.update_user_balance(user.id, -website['price'])
                    
                    # Create transaction record
                    await db_manager.create_transaction(
                        user_id=user.id,
                        transaction_type='purchase',
                        amount=-website['price'],
                        description=f"شراء موقع: {website['name']}"
                    )
                    
                    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    description = website.get('description', '')
                    description_text = f"\n📄 الوصف: {description}\n" if description else ""
                    
                    success_text = f"""
✅ تم شراء الموقع بنجاح!

🌐 الموقع: {website['name']}
🔗 الرابط: {website['url']}{description_text}
💰 المبلغ المدفوع: ${website['price']}
💳 رصيدك الجديد: ${user_balance - website['price']:.2f}

⚠️ احتفظ بالرابط والوصف في مكان آمن
                    """
                    
                    await safe_edit_message(query, success_text, reply_markup)
                else:
                    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await safe_edit_message(
                        query,
                        "❌ حدث خطأ في إتمام الشراء. يرجى المحاولة مرة أخرى.",
                        reply_markup
                    )
            else:
                keyboard = [
                    [InlineKeyboardButton("💸 إيداع USDT", callback_data='depositusdt')],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await safe_edit_message(
                    query,
                    "⚠️ رصيدك غير كافي لإتمام هذا الشراء.",
                    reply_markup
                )
        else:
            keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                "😔 هذا الموقع لم يعد متاحاً.",
                reply_markup
            )
    
    # Handle card order confirmation
    elif query.data.startswith('confirm_'):
        # Remove 'confirm_' prefix to get the full card_id
        card_id = query.data[8:]  # Remove 'confirm_' (8 characters)
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
                    
                    # Create notification for order bot to process
                    await create_order_notification(user, card, order_id)
                    
                    keyboard = [[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='start')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    success_text = f"""✅ تم إنشاء الطلب بنجاح!

🆔 رقم الطلب: {order_id}
🏷️ نوع البطاقة: {card['card_type']}
💰 المبلغ المدفوع: {card['price']} USDT

📨 تم إرسال إشعار للإدارة وسيتم إرسال تفاصيل البطاقة قريباً.

⏰ وقت التسليم المتوقع: 5-30 دقيقة"""
                    
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
    
    # Handle black website purchase
    elif query.data.startswith('buy_website_'):
        website_id = query.data[12:]  # Remove 'buy_website_' prefix
        website = await db_manager.get_black_website(website_id)
        
        if website:
            user_balance = await db_manager.get_user_balance(user.id)
            
            if user_balance >= website['price']:
                # Show confirmation dialog
                keyboard = [
                    [InlineKeyboardButton("✅ نعم، أريد الشراء", callback_data=f"confirm_buy_website_{website_id}")],
                    [InlineKeyboardButton("❌ إلغاء", callback_data='blacklist')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                confirmation_text = f"""
🌐 تأكيد شراء الموقع

📋 الموقع: {website['name']}
💰 السعر: ${website['price']}
💳 رصيدك الحالي: ${user_balance:.2f}

هل أنت متأكد من شراء هذا الموقع؟
                """
                await safe_edit_message(query, confirmation_text, reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("💸 إيداع USDT", callback_data='depositusdt')],
                    [InlineKeyboardButton("🔙 العودة للمواقع", callback_data='blacklist')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await safe_edit_message(
                    query,
                    f"⚠️ رصيدك غير كافي لشراء هذا الموقع.\n\n💰 السعر: ${website['price']}\n💳 رصيدك: ${user_balance:.2f}",
                    reply_markup
                )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للمواقع", callback_data='blacklist')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "😔 هذا الموقع لم يعد متاحاً.", reply_markup)
    

async def create_order_notification(user, card, order_id):
    """Create a notification for the order bot to process"""
    try:
        notification_data = {
            "order_id": order_id,
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "username": user.username
            },
            "card": {
                "card_type": card['card_type'],
                "country_name": card.get('country_name', 'غير محدد'),
                "price": card['price']
            },
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        notification_id = await db_manager.create_notification("new_order", notification_data)
        if notification_id:
            logging.info(f"Created notification {notification_id} for order {order_id}")
        else:
            logging.error(f"Failed to create notification for order {order_id}")
            
    except Exception as e:
        logging.error(f"Error creating order notification: {e}")


async def process_card_delivery_notifications(application):
    """Background task to process card delivery notifications"""
    while True:
        try:
            # Get pending card delivery notifications
            notifications = await db_manager.get_pending_notifications()
            
            for notification in notifications:
                if notification.get('type') == 'deliver_card':
                    await handle_card_delivery(application, notification)
                elif notification.get('type') == 'deliver_card_image':
                    await handle_card_image_delivery(application, notification)
                elif notification.get('type') == 'order_completed':
                    await handle_order_status_notification(application, notification)
                elif notification.get('type') == 'order_cancelled':
                    await handle_order_status_notification(application, notification)
                elif notification.get('type') == 'balance_updated':
                    await handle_balance_notification(application, notification)
                elif notification.get('type') == 'user_blocked':
                    await handle_block_notification(application, notification)
                elif notification.get('type') == 'user_unblocked':
                    await handle_block_notification(application, notification)
                    
            # Wait 5 seconds before checking again
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in card delivery notification processing: {e}")
            await asyncio.sleep(10)  # Wait longer on error


async def handle_card_delivery(application, notification):
    """Handle card delivery notification"""
    try:
        data = notification.get('data', {})
        user_id = data.get('user_id')
        order_id = data.get('order_id')
        card_details = data.get('card_details', {})
        
        if not user_id or not card_details:
            logger.error(f"Invalid card delivery notification data: {data}")
            # Mark invalid notifications as processed to avoid infinite retry
            await db_manager.mark_notification_processed(notification['notification_id'])
            return
        
        # Format card details message
        card_message = f"""🎉 تم تجهيز بطاقتك بنجاح!

📋 تفاصيل البطاقة:
🆔 رقم الطلب: {order_id}
👤 اسم حامل البطاقة: {card_details.get('holder_name')}
💳 رقم البطاقة: {card_details.get('card_number')}
🔒 رمز CVV: {card_details.get('cvv')}

⚠️ تعليمات مهمة:
• احتفظ بهذه المعلومات في مكان آمن
• لا تشارك تفاصيل البطاقة مع أي شخص
• تأكد من استخدام البطاقة في المواقع الآمنة فقط

✅ شكراً لاستخدام خدماتنا!"""
        
        await application.bot.send_message(
            chat_id=user_id,
            text=card_message
        )
        
        # Mark notification as processed
        await db_manager.mark_notification_processed(notification['notification_id'])
        logger.info(f"Delivered card details for order {order_id} to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling card delivery notification {notification.get('notification_id')}: {e}")
        # For certain errors (like user blocked bot), mark as processed to avoid infinite retry
        error_str = str(e).lower()
        if any(phrase in error_str for phrase in ['blocked', 'not found', 'forbidden', 'chat not found']):
            logger.warning(f"User {user_id} appears to have blocked the bot or chat not found. Marking notification as processed.")
            await db_manager.mark_notification_processed(notification['notification_id'])


async def handle_card_image_delivery(application, notification):
    """Handle card image delivery notification"""
    try:
        data = notification.get('data', {})
        user_id = data.get('user_id')
        order_id = data.get('order_id')
        image_data_base64 = data.get('image_data')
        
        if not user_id or not image_data_base64:
            logger.error(f"Invalid card image delivery notification data: {data}")
            # Mark invalid notifications as processed to avoid infinite retry
            await db_manager.mark_notification_processed(notification['notification_id'])
            return
        
        # Decode base64 image data
        image_data = base64.b64decode(image_data_base64)
        image_io = io.BytesIO(image_data)
        
        # Send the image with a caption
        caption = f"""🎉 تم تجهيز بطاقتك بنجاح!

🆔 رقم الطلب: {order_id}
📷 تفاصيل البطاقة في الصورة أعلاه

⚠️ تعليمات مهمة:
• احتفظ بهذه الصورة في مكان آمن
• لا تشارك تفاصيل البطاقة مع أي شخص
• تأكد من استخدام البطاقة في المواقع الآمنة فقط

✅ شكراً لاستخدام خدماتنا!"""
        
        await application.bot.send_photo(
            chat_id=user_id,
            photo=image_io,
            caption=caption
        )
        
        # Mark notification as processed
        await db_manager.mark_notification_processed(notification['notification_id'])
        logger.info(f"Delivered card image for order {order_id} to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling card image delivery notification {notification.get('notification_id')}: {e}")
        # For certain errors (like user blocked bot), mark as processed to avoid infinite retry
        error_str = str(e).lower()
        if any(phrase in error_str for phrase in ['blocked', 'not found', 'forbidden', 'chat not found']):
            logger.warning(f"User {user_id} appears to have blocked the bot or chat not found. Marking notification as processed.")
            await db_manager.mark_notification_processed(notification['notification_id'])




async def startup_database(application):
    """Initialize database connection and start notification processor"""
    try:
        await db_manager.connect()
        logging.info("Database connected successfully")
        
        # Set bot commands to only show /start in the menu
        commands = [
            BotCommand("start", "بدء استخدام البوت")
        ]
        await application.bot.set_my_commands(commands)
        logging.info("Bot commands set successfully")
        
        # Start the notification processor for card deliveries
        asyncio.create_task(process_card_delivery_notifications(application))
        logging.info("Started card delivery notification processor")
        
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        raise


async def handle_order_status_notification(application, notification):
    """Handle order status change notifications (completed/cancelled)"""
    try:
        data = notification.get('data', {})
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            logger.error(f"Invalid order status notification data: {data}")
            await db_manager.mark_notification_processed(notification['notification_id'])
            return
        
        # Send notification message to user
        await application.bot.send_message(
            chat_id=user_id,
            text=message
        )
        
        # Mark notification as processed
        await db_manager.mark_notification_processed(notification['notification_id'])
        logger.info(f"Order status notification sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling order status notification {notification['notification_id']}: {e}")


async def handle_balance_notification(application, notification):
    """Handle balance update notifications"""
    try:
        data = notification.get('data', {})
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            logger.error(f"Invalid balance notification data: {data}")
            await db_manager.mark_notification_processed(notification['notification_id'])
            return
        
        # Send balance update message to user
        await application.bot.send_message(
            chat_id=user_id,
            text=message
        )
        
        # Mark notification as processed
        await db_manager.mark_notification_processed(notification['notification_id'])
        logger.info(f"Balance notification sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling balance notification {notification['notification_id']}: {e}")


async def handle_block_notification(application, notification):
    """Handle user block/unblock notifications"""
    try:
        data = notification.get('data', {})
        user_id = data.get('user_id')
        message = data.get('message')
        
        if not user_id or not message:
            logger.error(f"Invalid block notification data: {data}")
            await db_manager.mark_notification_processed(notification['notification_id'])
            return
        
        # Send block/unblock message to user
        await application.bot.send_message(
            chat_id=user_id,
            text=message
        )
        
        # Mark notification as processed
        await db_manager.mark_notification_processed(notification['notification_id'])
        logger.info(f"Block notification sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling block notification {notification['notification_id']}: {e}")


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
    
    # Reduce httpx logging noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Get bot token from environment or use default
    TOKEN = os.getenv('BOT_TOKEN', "7857065897:AAGM-nDNhZ8DDaTFGTt3g4CDlHXb355K5ps")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add startup and shutdown handlers
    application.post_init = startup_database
    application.post_shutdown = shutdown_database
    
    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Get webhook configuration
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8443'))
    USE_WEBHOOKS = os.getenv('USE_WEBHOOKS', 'false').lower() == 'true'
    
    if USE_WEBHOOKS and WEBHOOK_URL:
        # Run with webhooks
        logging.info(f"Starting bot with webhooks on port {WEBHOOK_PORT}...")
        logging.info(f"Webhook URL: {WEBHOOK_URL}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook",
            allowed_updates=Update.ALL_TYPES
        )
    else:
        # Fallback to polling
        logging.info("Starting bot with polling...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            poll_interval=2.0,  # Check every 2 seconds instead of default 0.1
            timeout=10          # Wait up to 10 seconds for updates
        )

if __name__ == '__main__':
    main()