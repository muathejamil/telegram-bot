import os
import logging
import asyncio
import base64
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from database import db_manager
from telegram.error import BadRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Predefined countries for easy selection
COUNTRIES = {
    'US': {'name': 'الولايات المتحدة', 'flag': '🇺🇸'},
    'UK': {'name': 'المملكة المتحدة', 'flag': '🇬🇧'},
    'CA': {'name': 'كندا', 'flag': '🇨🇦'},
    'DE': {'name': 'ألمانيا', 'flag': '🇩🇪'},
    'FR': {'name': 'فرنسا', 'flag': '🇫🇷'},
    'IT': {'name': 'إيطاليا', 'flag': '🇮🇹'},
    'ES': {'name': 'إسبانيا', 'flag': '🇪🇸'},
    'AU': {'name': 'أستراليا', 'flag': '🇦🇺'},
    'JP': {'name': 'اليابان', 'flag': '🇯🇵'},
    'KR': {'name': 'كوريا الجنوبية', 'flag': '🇰🇷'},
    'AE': {'name': 'الإمارات العربية المتحدة', 'flag': '🇦🇪'},
    'SA': {'name': 'المملكة العربية السعودية', 'flag': '🇸🇦'},
    'TR': {'name': 'تركيا', 'flag': '🇹🇷'},
    'NL': {'name': 'هولندا', 'flag': '🇳🇱'},
    'SE': {'name': 'السويد', 'flag': '🇸🇪'},
    'IL': {'name': 'إسرائيل', 'flag': '🇮🇱'},
}


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


async def start_order_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command for the order management bot"""
    user = update.effective_user
    
    # Check if user is admin (you can implement admin check logic)
    admin_id = os.getenv('ADMIN_USER_ID')
    if not admin_id or str(user.id) != admin_id:
        await update.message.reply_text('عذراً، هذا البوت مخصص للإدارة فقط.')
        return
    
    keyboard = [
        [InlineKeyboardButton("📋 الطلبات المعلقة", callback_data='pending_orders')],
        [InlineKeyboardButton("✅ الطلبات المكتملة", callback_data='completed_orders')],
        [InlineKeyboardButton("💳 إدارة البطاقات", callback_data='manage_cards')],
        [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data='manage_users')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='statistics')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    current_time = datetime.now().strftime('%H:%M')
    menu_text = f"مرحبًا بك في لوحة الإدارة!\n\n🕐 آخر تحديث: {current_time}"
    await update.message.reply_text(menu_text, reply_markup=reply_markup)


async def order_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks for the order management bot"""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    
    # Check if user is admin
    admin_id = os.getenv('ADMIN_USER_ID')
    if not admin_id or str(user.id) != admin_id:
        await safe_edit_message(query, 'عذراً، هذا البوت مخصص للإدارة فقط.')
        return
    
    if query.data == 'pending_orders':
        # Get pending orders from database
        orders = await db_manager.get_pending_orders()  # You'll need to implement this
        
        if orders:
            keyboard = []
            for order in orders[:10]:  # Show first 10 orders
                order_text = f"طلب #{order['order_id']} - {order['card_type']}"
                keyboard.append([InlineKeyboardButton(
                    order_text,
                    callback_data=f"order_{order['order_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                f"📋 الطلبات المعلقة ({len(orders)}):\n\nاختر طلباً لعرض التفاصيل:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                "✅ لا توجد طلبات معلقة حالياً",
                reply_markup
            )
    
    elif query.data == 'completed_orders':
        # Similar implementation for completed orders
        keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "✅ الطلبات المكتملة\n\n(قيد التطوير)",
            reply_markup
        )
    
    elif query.data == 'manage_cards':
        # Card management functionality
        keyboard = [
            [InlineKeyboardButton("➕ إضافة بطاقة جديدة", callback_data='add_card')],
            [InlineKeyboardButton("📋 عرض البطاقات", callback_data='view_cards')],
            [InlineKeyboardButton("📝 تعديل البطاقات", callback_data='edit_cards')],
            [InlineKeyboardButton("🔄 تفعيل/إلغاء البطاقات", callback_data='toggle_cards')],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "💳 إدارة البطاقات\n\nاختر العملية المطلوبة:",
            reply_markup
        )
    
    elif query.data == 'start':
        # Return to main menu
        keyboard = [
            [InlineKeyboardButton("📋 الطلبات المعلقة", callback_data='pending_orders')],
            [InlineKeyboardButton("✅ الطلبات المكتملة", callback_data='completed_orders')],
            [InlineKeyboardButton("💳 إدارة البطاقات", callback_data='manage_cards')],
            [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data='manage_users')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='statistics')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        current_time = datetime.now().strftime('%H:%M')
        menu_text = f"مرحبًا بك في لوحة الإدارة!\n\n🕐 آخر تحديث: {current_time}"
        
        await safe_edit_message(query, menu_text, reply_markup, "تم تحديث القائمة ✅")
    
    # Handle order action buttons
    elif query.data.startswith('sent_'):
        order_id = query.data[5:]  # Remove 'sent_' prefix
        # Ask admin to provide card details
        keyboard = [
            [InlineKeyboardButton("📝 إدخال تفاصيل البطاقة", callback_data=f"input_card_{order_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data='start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query, 
            f"📋 الطلب #{order_id}\n\nيرجى إدخال تفاصيل البطاقة للعميل:",
            reply_markup
        )
    
    elif query.data.startswith('cancel_'):
        order_id = query.data[7:]  # Remove 'cancel_' prefix
        await db_manager.update_order_status(order_id, 'cancelled')
        await safe_edit_message(query, f"❌ تم إلغاء الطلب #{order_id}")
    
    elif query.data.startswith('details_'):
        order_id = query.data[8:]  # Remove 'details_' prefix
        order = await db_manager.get_order_by_id(order_id)
        if order:
            details_text = f"""
📋 تفاصيل الطلب #{order_id}

🆔 معرف الطلب: {order['order_id']}
👤 معرف المستخدم: {order['user_id']}
🏷️ معرف البطاقة: {order['card_id']}
🌍 كود الدولة: {order['country_code']}
💰 المبلغ: {order['amount']} USDT
📊 الحالة: {order.get('status', 'pending')}
📅 تاريخ الإنشاء: {order.get('created_at', 'غير محدد')}
            """
            keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, details_text, reply_markup)
        else:
            await safe_edit_message(query, f"❌ لم يتم العثور على الطلب #{order_id}")
    
    # Handle card management
    elif query.data == 'add_card':
        # Start card addition process
        context.user_data['adding_card'] = True
        context.user_data['card_step'] = 'card_type'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_cards')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "➕ إضافة بطاقات جديدة (إضافة مجمعة)\n\n1️⃣ يرجى إدخال نوع البطاقة (مثال: VISA 25$):",
            reply_markup
        )
    
    elif query.data == 'view_cards':
        # Show all cards
        cards = await get_all_cards_for_admin()
        if cards:
            cards_text = "📋 جميع البطاقات:\n\n"
            for card in cards[:10]:  # Show first 10 cards
                status = "✅ متاحة" if card.get('is_available') else "❌ غير متاحة"
                cards_text += f"🏷️ {card['card_type']}\n"
                cards_text += f"🌍 {card.get('country_name', 'غير محدد')}\n"
                cards_text += f"💰 {card['price']} USDT\n"
                cards_text += f"📊 {status}\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, cards_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "📋 لا توجد بطاقات في النظام حالياً", reply_markup)
    
    elif query.data == 'edit_cards':
        keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, "📝 تعديل البطاقات\n\n(قيد التطوير)", reply_markup)
    
    elif query.data == 'toggle_cards':
        keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, "🔄 تفعيل/إلغاء البطاقات\n\n(قيد التطوير)", reply_markup)
    
    # Handle country selection for card addition
    elif query.data.startswith('country_select_'):
        country_code = query.data.split('_')[2]  # Extract country code
        if country_code in COUNTRIES:
            context.user_data['country_code'] = country_code
            context.user_data['country_name'] = COUNTRIES[country_code]['name']
            context.user_data['card_step'] = 'price'
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                f"✅ الدولة: {COUNTRIES[country_code]['flag']} {COUNTRIES[country_code]['name']}\n\n3️⃣ يرجى إدخال سعر البطاقة بالدولار (مثال: 25.00):",
                reply_markup
            )
    
    # Handle card details input
    elif query.data.startswith('input_card_'):
        order_id = query.data[11:]  # Remove 'input_card_' prefix
        # Store the order_id in user context for the next messages
        context.user_data['awaiting_card_image'] = order_id
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            f"📷 إرسال صورة البطاقة للطلب #{order_id}\n\n📤 يرجى إرسال صورة تحتوي على تفاصيل البطاقة:",
            reply_markup
        )


async def handle_card_image_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle image upload for card details"""
    user = update.effective_user
    
    # Check if user is admin
    admin_id = os.getenv('ADMIN_USER_ID')
    if not admin_id or str(user.id) != admin_id:
        return
    
    # Check if we're waiting for card image
    if 'awaiting_card_image' not in context.user_data:
        return
    
    order_id = context.user_data['awaiting_card_image']
    
    # Check if message has photo
    if not update.message.photo:
        await update.message.reply_text("❌ يرجى إرسال صورة وليس نص. أرسل صورة البطاقة.")
        return
    
    try:
        # Get the highest resolution photo
        photo = update.message.photo[-1]
        
        # Download the image file
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()
        
        # Create notification for customer bot to send image to user
        await create_card_image_delivery_notification(order_id, file_bytes)
        
        # Update order status
        await db_manager.update_order_status(order_id, 'completed')
        
        # Clear user context
        context.user_data.clear()
        
        keyboard = [[InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        confirmation_text = f"""
✅ تم إرسال صورة البطاقة بنجاح!

🆔 رقم الطلب: {order_id}
📷 تم إرسال الصورة للعميل عبر البوت الرئيسي.

⏰ وقت الإرسال: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.message.reply_text(confirmation_text, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error handling card image upload: {e}")
        await update.message.reply_text("❌ حدث خطأ في معالجة الصورة. يرجى المحاولة مرة أخرى.")


async def handle_card_addition_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input for adding new cards"""
    user = update.effective_user
    
    # Check if user is admin
    admin_id = os.getenv('ADMIN_USER_ID')
    if not admin_id or str(user.id) != admin_id:
        return
    
    # Check if we're adding a card
    if not context.user_data.get('adding_card'):
        return
    
    step = context.user_data.get('card_step')
    text = update.message.text
    
    try:
        if step == 'card_type':
            context.user_data['card_type'] = text
            context.user_data['card_step'] = 'country_selection'
            
            # Create country selection keyboard
            keyboard = []
            countries_list = list(COUNTRIES.items())
            
            # Create rows of 2 countries each
            for i in range(0, len(countries_list), 2):
                row = []
                for j in range(2):
                    if i + j < len(countries_list):
                        code, info = countries_list[i + j]
                        row.append(InlineKeyboardButton(
                            f"{info['flag']} {code}",
                            callback_data=f"country_select_{code}"
                        ))
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data='manage_cards')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ نوع البطاقة: {text}\n\n2️⃣ اختر الدولة:",
                reply_markup=reply_markup
            )
        
        elif step == 'price':
            try:
                price = float(text)
                context.user_data['price'] = price
                context.user_data['card_step'] = 'value'
                
                keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_cards')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ السعر: ${price}\n\n4️⃣ يرجى إدخال قيمة البطاقة (مثال: 25.00):",
                    reply_markup=reply_markup
                )
            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح للسعر (مثال: 25.00)")
        
        elif step == 'value':
            try:
                value = float(text)
                context.user_data['value'] = value
                context.user_data['card_step'] = 'quantity'
                
                keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_cards')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ قيمة البطاقة: ${value}\n\n5️⃣ يرجى إدخال عدد البطاقات المطلوب إنشاؤها (مثال: 5):",
                    reply_markup=reply_markup
                )
            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح للقيمة (مثال: 25.00)")
        
        elif step == 'quantity':
            try:
                quantity = int(text)
                if quantity <= 0 or quantity > 100:
                    await update.message.reply_text("❌ يرجى إدخال عدد صحيح بين 1 و 100")
                    return
                
                # Create multiple cards
                card_base_data = {
                    'card_type': context.user_data['card_type'],
                    'country_code': context.user_data['country_code'],
                    'country_name': context.user_data['country_name'],
                    'price': context.user_data['price'],
                    'value': context.user_data['value'],
                    'currency': 'USD',
                    'is_available': True,
                    'created_at': datetime.utcnow()
                }
                
                # Add multiple cards to database
                success_count = await add_bulk_cards_to_database(card_base_data, quantity)
                
                # Clear user context
                context.user_data.clear()
                
                if success_count > 0:
                    keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    country_info = COUNTRIES.get(card_base_data['country_code'], {})
                    flag = country_info.get('flag', '🌍')
                    
                    success_text = f"""
✅ تم إضافة البطاقات بنجاح!

📋 تفاصيل البطاقات:
🏷️ النوع: {card_base_data['card_type']}
🌍 الدولة: {flag} {card_base_data['country_name']}
💰 السعر: ${card_base_data['price']}
💳 القيمة: ${card_base_data['value']}
🔢 العدد: {success_count} بطاقة
📊 الحالة: متاحة

⏰ تم الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """
                    
                    await update.message.reply_text(success_text, reply_markup=reply_markup)
                else:
                    keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text("❌ حدث خطأ في إضافة البطاقات. يرجى المحاولة مرة أخرى.", reply_markup=reply_markup)
                
            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح للعدد (مثال: 5)")
    
    except Exception as e:
        logger.error(f"Error handling card addition: {e}")
        context.user_data.clear()
        await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة مرة أخرى.")


async def create_card_image_delivery_notification(order_id: str, image_data: bytearray):
    """Create notification for customer bot to deliver card image"""
    try:
        # Get order details to find the user
        order = await db_manager.get_order_by_id(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return
        
        # Convert bytearray to base64 for storage
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        notification_data = {
            "order_id": order_id,
            "user_id": order.get('user_id'),
            "image_data": image_base64
        }
        
        notification_id = await db_manager.create_notification("deliver_card_image", notification_data)
        if notification_id:
            logger.info(f"Created card image delivery notification {notification_id} for order {order_id}")
        else:
            logger.error(f"Failed to create card image delivery notification for order {order_id}")
            
    except Exception as e:
        logger.error(f"Error creating card image delivery notification: {e}")


async def get_all_cards_for_admin():
    """Get all cards for admin view"""
    try:
        # Get all cards from database
        cursor = db_manager.cards.find({}).sort("created_at", -1)
        cards = await cursor.to_list(length=None)
        return cards
    except Exception as e:
        logger.error(f"Error getting cards for admin: {e}")
        return []


async def add_card_to_database(card_data):
    """Add a new card to the database"""
    try:
        # First, ensure the country exists in the countries collection
        await ensure_country_exists(card_data['country_code'], card_data['country_name'])
        
        # Generate unique card ID
        card_id = f"{card_data['country_code']}_{card_data['card_type'].replace(' ', '_')}_{int(card_data['value'])}"
        card_data['card_id'] = card_id
        
        # Insert card into database
        result = await db_manager.cards.insert_one(card_data)
        
        if result.inserted_id:
            logger.info(f"Added new card: {card_id}")
            return True
        else:
            logger.error(f"Failed to add card: {card_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding card to database: {e}")
        return False


async def add_bulk_cards_to_database(card_base_data, quantity):
    """Add multiple cards to the database"""
    try:
        # First, ensure the country exists in the countries collection
        await ensure_country_exists(card_base_data['country_code'], card_base_data['country_name'])
        
        success_count = 0
        
        for i in range(quantity):
            # Create unique card ID for each card
            card_data = card_base_data.copy()
            card_id = f"{card_data['country_code']}_{card_data['card_type'].replace(' ', '_')}_{int(card_data['value'])}_{i+1:03d}"
            card_data['card_id'] = card_id
            
            # Insert card into database
            result = await db_manager.cards.insert_one(card_data)
            
            if result.inserted_id:
                success_count += 1
                logger.info(f"Added bulk card {i+1}/{quantity}: {card_id}")
            else:
                logger.error(f"Failed to add bulk card {i+1}/{quantity}: {card_id}")
        
        logger.info(f"Successfully added {success_count}/{quantity} cards")
        return success_count
        
    except Exception as e:
        logger.error(f"Error adding bulk cards to database: {e}")
        return 0


async def ensure_country_exists(country_code, country_name):
    """Ensure a country exists in the countries collection"""
    try:
        # Check if country already exists
        existing_country = await db_manager.countries.find_one({"code": country_code})
        
        if not existing_country:
            # Get flag from COUNTRIES dict
            country_info = COUNTRIES.get(country_code, {})
            flag = country_info.get('flag', '🌍')
            
            # Add country to countries collection
            country_data = {
                "code": country_code,
                "name": country_name,
                "flag": flag,
                "is_active": True,
                "created_at": datetime.utcnow()
            }
            
            result = await db_manager.countries.insert_one(country_data)
            if result.inserted_id:
                logger.info(f"Added new country: {country_code} - {country_name}")
            else:
                logger.error(f"Failed to add country: {country_code}")
        else:
            logger.info(f"Country already exists: {country_code}")
            
    except Exception as e:
        logger.error(f"Error ensuring country exists: {e}")


async def process_notifications(application):
    """Background task to process pending notifications"""
    while True:
        try:
            # Get pending notifications
            notifications = await db_manager.get_pending_notifications()
            
            for notification in notifications:
                await handle_notification(application, notification)
                
            # Wait 5 seconds before checking again
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in notification processing: {e}")
            await asyncio.sleep(10)  # Wait longer on error


async def handle_notification(application, notification):
    """Handle a specific notification"""
    try:
        notification_type = notification.get('type')
        data = notification.get('data', {})
        
        if notification_type == 'new_order':
            await send_order_notification(application, data)
        
        # Mark notification as processed
        await db_manager.mark_notification_processed(notification['notification_id'])
        logger.info(f"Processed notification {notification['notification_id']}")
        
    except Exception as e:
        logger.error(f"Error handling notification {notification.get('notification_id')}: {e}")


async def send_order_notification(application, data):
    """Send order notification to admin"""
    try:
        admin_id = os.getenv('ADMIN_USER_ID')
        if not admin_id:
            logger.warning("ADMIN_USER_ID not set in environment variables")
            return
        
        admin_id = int(admin_id)
        user_data = data.get('user', {})
        card_data = data.get('card', {})
        
        notification_text = f"""
🔔 طلب جديد!

👤 معلومات المستخدم:
🆔 ID: {user_data.get('id')}
👤 الاسم: {user_data.get('first_name', 'غير محدد')}
📧 اسم المستخدم: @{user_data.get('username', 'غير محدد')}

🛒 تفاصيل الطلب:
🆔 رقم الطلب: {data.get('order_id')}
🏷️ نوع البطاقة: {card_data.get('card_type')}
🌍 الدولة: {card_data.get('country_name')}
💰 المبلغ: {card_data.get('price')} USDT

⏰ وقت الطلب: {data.get('timestamp')}

يرجى إرسال تفاصيل البطاقة للمستخدم.
        """
        
        # Create keyboard with action buttons
        keyboard = [
            [InlineKeyboardButton("✅ تم الإرسال", callback_data=f"sent_{data.get('order_id')}")],
            [InlineKeyboardButton("❌ إلغاء الطلب", callback_data=f"cancel_{data.get('order_id')}")],
            [InlineKeyboardButton("📋 عرض التفاصيل", callback_data=f"details_{data.get('order_id')}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await application.bot.send_message(
            chat_id=admin_id,
            text=notification_text,
            reply_markup=reply_markup
        )
        
        logger.info(f"Sent order notification for order {data.get('order_id')} to admin {admin_id}")
        
    except Exception as e:
        logger.error(f"Error sending order notification: {e}")


async def startup_database(application):
    """Initialize database connection and start notification processor"""
    try:
        await db_manager.connect()
        logging.info("Order bot database connected successfully")
        
        # Start the notification processor in the background
        asyncio.create_task(process_notifications(application))
        logging.info("Started notification processor")
        
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        raise


async def shutdown_database(application):
    """Close database connection"""
    await db_manager.disconnect()
    logging.info("Order bot database disconnected")


def main() -> None:
    """Main function to start the order management bot"""
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Get bot token from environment
    ORDER_BOT_TOKEN = os.getenv('ORDER_BOT_TOKEN')
    if not ORDER_BOT_TOKEN:
        logging.error("ORDER_BOT_TOKEN not found in environment variables")
        return
    
    # Create application
    application = Application.builder().token(ORDER_BOT_TOKEN).build()
    
    # Add startup and shutdown handlers
    application.post_init = startup_database
    application.post_shutdown = shutdown_database
    
    # Add command and message handlers
    application.add_handler(CommandHandler("start", start_order_bot))
    application.add_handler(CallbackQueryHandler(order_button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_card_image_upload))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_card_addition_text))
    
    # Run the bot until the user presses Ctrl-C
    logging.info("Starting order management bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
