import os
import logging
import asyncio
import base64
from datetime import datetime, UTC
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
from database import db_manager
from telegram.error import BadRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce httpx logging noise
logging.getLogger("httpx").setLevel(logging.WARNING)

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
        [InlineKeyboardButton("🌐 إدارة المواقع السوداء", callback_data='manage_black_websites')],
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
        orders = await db_manager.get_pending_orders()
        
        if orders:
            keyboard = []
            for order in orders[:15]:  # Show first 15 orders
                # Get user info for display
                user_info = await db_manager.get_user(order['user_id'])
                username = user_info.get('username', 'غير محدد') if user_info else 'غير محدد'
                
                # Format order creation time
                created_at = order.get('created_at', datetime.now(UTC))
                if isinstance(created_at, datetime):
                    time_str = created_at.strftime('%m-%d %H:%M')
                else:
                    time_str = 'غير محدد'
                
                order_text = f"📋 #{order['order_id'][:8]} | @{username} | {time_str}"
                keyboard.append([InlineKeyboardButton(
                    order_text,
                    callback_data=f"pending_order_{order['order_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔄 تحديث القائمة", callback_data='pending_orders')])
            keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                f"📋 الطلبات المعلقة ({len(orders)})\n\n⏳ طلبات تحتاج إلى إكمال:\n\nاختر طلباً لعرض التفاصيل وإكماله:",
                reply_markup
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث القائمة", callback_data='pending_orders')],
                [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                "✅ لا توجد طلبات معلقة حالياً\n\n🎉 جميع الطلبات مكتملة!",
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
            [InlineKeyboardButton("🗑️ حذف البطاقات", callback_data='remove_cards')],
            # [InlineKeyboardButton("🔄 تفعيل/إلغاء البطاقات", callback_data='toggle_cards')],
            [InlineKeyboardButton("🗂️ عرض البطاقات المحذوفة", callback_data='view_deleted_cards')],
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
            [InlineKeyboardButton("🌐 إدارة المواقع السوداء", callback_data='manage_black_websites')],
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
    
    # Handle individual pending orders
    elif query.data.startswith('pending_order_'):
        order_id = query.data[14:]  # Remove 'pending_order_' prefix
        order = await db_manager.get_order_by_id(order_id)
        
        if order:
            # Get user and card information
            user_info = await db_manager.get_user(order['user_id'])
            card_info = await get_card_by_id(order['card_id'])
            
            username = user_info.get('username', 'غير محدد') if user_info else 'غير محدد'
            first_name = user_info.get('first_name', 'غير محدد') if user_info else 'غير محدد'
            
            # Format timestamps
            created_at = order.get('created_at', datetime.now(UTC))
            if isinstance(created_at, datetime):
                created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_str = 'غير محدد'
            
            # Card details
            if card_info:
                country_info = COUNTRIES.get(card_info['country_code'], {})
                flag = country_info.get('flag', '🌍')
                card_details = f"{card_info['card_type']} - {flag} {card_info['country_name']}"
                card_price = f"${card_info['price']}"
                card_value = f"${card_info['value']}"
            else:
                card_details = "بطاقة غير موجودة"
                card_price = "غير محدد"
                card_value = "غير محدد"
            
            order_details = f"""
📋 تفاصيل الطلب المعلق

🆔 رقم الطلب: {order['order_id']}
👤 العميل: {first_name} (@{username})
🆔 معرف العميل: {order['user_id']}

💳 البطاقة المطلوبة:
{card_details}
💰 السعر: {card_price}
💎 القيمة: {card_value}

📊 حالة الطلب: ⏳ معلق
📅 تاريخ الطلب: {created_str}
💵 المبلغ المدفوع: ${order.get('amount', 0)}

⚡ اختر الإجراء المطلوب:
            """
            
            keyboard = [
                [InlineKeyboardButton("📤 إرسال تفاصيل البطاقة", callback_data=f"send_card_{order_id}")],
                [InlineKeyboardButton("✅ تأكيد اكتمال الطلب", callback_data=f"complete_order_{order_id}")],
                [InlineKeyboardButton("❌ إلغاء الطلب", callback_data=f"cancel_order_{order_id}")],
                [InlineKeyboardButton("🔙 العودة للطلبات المعلقة", callback_data='pending_orders')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(query, order_details, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للطلبات المعلقة", callback_data='pending_orders')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"❌ لم يتم العثور على الطلب #{order_id}", reply_markup)
    
    # Handle order completion
    elif query.data.startswith('complete_order_'):
        order_id = query.data[15:]  # Remove 'complete_order_' prefix
        success = await complete_order(order_id)
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 العودة للطلبات المعلقة", callback_data='pending_orders')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                f"✅ تم إكمال الطلب #{order_id} بنجاح!\n\n🎉 تم إشعار العميل بإكمال الطلب.",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للطلبات المعلقة", callback_data='pending_orders')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"❌ فشل في إكمال الطلب #{order_id}", reply_markup)
    
    # Handle order cancellation
    elif query.data.startswith('cancel_order_'):
        order_id = query.data[13:]  # Remove 'cancel_order_' prefix
        order = await db_manager.get_order_by_id(order_id)
        
        if order:
            keyboard = [
                [InlineKeyboardButton("✅ نعم، إلغاء الطلب", callback_data=f"confirm_cancel_{order_id}")],
                [InlineKeyboardButton("❌ لا، العودة للطلب", callback_data=f"pending_order_{order_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                f"⚠️ تأكيد إلغاء الطلب\n\nهل أنت متأكد من إلغاء الطلب #{order_id}?\n\n⚠️ سيتم إشعار العميل بإلغاء الطلب.",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للطلبات المعلقة", callback_data='pending_orders')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"❌ لم يتم العثور على الطلب #{order_id}", reply_markup)
    
    elif query.data.startswith('confirm_cancel_'):
        order_id = query.data[15:]  # Remove 'confirm_cancel_' prefix
        success = await cancel_order(order_id)
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 العودة للطلبات المعلقة", callback_data='pending_orders')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                f"❌ تم إلغاء الطلب #{order_id}\n\n📧 تم إشعار العميل بإلغاء الطلب.",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للطلبات المعلقة", callback_data='pending_orders')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"❌ فشل في إلغاء الطلب #{order_id}", reply_markup)
    
    # Handle sending card details (reuse existing functionality)
    elif query.data.startswith('send_card_'):
        order_id = query.data[10:]  # Remove 'send_card_' prefix
        # Store the order_id in user context for the next messages
        context.user_data['awaiting_card_image'] = order_id
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f'pending_order_{order_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            f"📷 إرسال صورة البطاقة للطلب #{order_id}\n\n📤 يرجى إرسال صورة تحتوي على تفاصيل البطاقة:",
            reply_markup
        )
    
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
                available_count = card.get('number_of_available_cards', 0)
                status = f"✅ متاحة ({available_count})" if card.get('is_available') and available_count > 0 else "❌ غير متاحة"
                cards_text += f"🏷️ {card['card_type']}\n"
                cards_text += f"🌍 {card.get('country_name', 'غير محدد')}\n"
                cards_text += f"💰 {card['price']} USDT\n"
                cards_text += f"💳 القيمة: {card.get('value', card['price'])} USDT\n"
                cards_text += f"📊 {status}\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, cards_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "📋 لا توجد بطاقات في النظام حالياً", reply_markup)
    
    elif query.data == 'edit_cards':
        # Show cards for editing
        cards = await get_all_cards_for_admin()
        if cards:
            keyboard = []
            for card in cards[:20]:  # Limit to 20 cards to avoid message length issues
                available_count = card.get('number_of_available_cards', 0)
                status_icon = "✅" if card['is_available'] and available_count > 0 else "❌"
                card_text = f"{status_icon} {card['card_type']} - {card['country_code']} (${card['price']}) ({available_count})"
                keyboard.append([InlineKeyboardButton(
                    card_text,
                    callback_data=f"edit_card_{card['card_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                "📝 تعديل البطاقات\n\nاختر البطاقة التي تريد تعديلها:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لا توجد بطاقات للتعديل", reply_markup)
    
    elif query.data == 'toggle_cards':
        # Show cards for toggling availability
        cards = await get_all_cards_for_admin()
        if cards:
            keyboard = []
            for card in cards[:20]:  # Limit to 20 cards
                status_icon = "✅" if card['is_available'] else "❌"
                action_text = "إلغاء" if card['is_available'] else "تفعيل"
                card_text = f"{status_icon} {card['card_type']} - {card['country_code']} ({action_text})"
                keyboard.append([InlineKeyboardButton(
                    card_text,
                    callback_data=f"toggle_card_{card['card_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                "🔄 تفعيل/إلغاء البطاقات\n\nاختر البطاقة لتغيير حالتها:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لا توجد بطاقات للتعديل", reply_markup)
    
    elif query.data == 'remove_cards':
        # Show grouped cards for removal
        grouped_cards = await db_manager.get_grouped_cards_for_deletion()
        if grouped_cards:
            keyboard = []
            for card_group in grouped_cards:
                # Get country flag
                country_info = COUNTRIES.get(card_group['country_code'], {})
                flag = country_info.get('flag', '🌍')
                
                # Format: "Visa - IL ($20.0) (5) ❌"
                card_text = f"{card_group['card_type']} - {flag} {card_group['country_code']} (${card_group['price']}) ({card_group['count']}) ❌"
                
                # Use callback data format: remove_group_countrycode_cardtype_price
                callback_data = f"remove_group_{card_group['country_code']}_{card_group['card_type'].replace(' ', '_')}_{card_group['price']}"
                keyboard.append([InlineKeyboardButton(
                    card_text,
                    callback_data=callback_data
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                "🗑️ حذف البطاقات\n\n⚠️ تحذير: سيتم حذف جميع البطاقات في المجموعة نهائياً!\nاختر المجموعة التي تريد حذفها:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لا توجد بطاقات للحذف", reply_markup)
    
    elif query.data == 'view_deleted_cards':
        # Show deleted cards
        deleted_cards = await get_deleted_cards_for_admin()
        if deleted_cards:
            cards_text = "🗂️ البطاقات المحذوفة:\n\n"
            for i, card in enumerate(deleted_cards[:15], 1):  # Limit to 15 cards
                country_info = COUNTRIES.get(card['country_code'], {})
                flag = country_info.get('flag', '🌍')
                deleted_at = card.get('deleted_at', 'غير محدد')
                if isinstance(deleted_at, datetime):
                    deleted_at = deleted_at.strftime('%Y-%m-%d %H:%M')
                
                cards_text += f"{i}. 🗑️ {card['card_type']} - {flag} {card['country_code']}\n"
                cards_text += f"   💰 السعر: ${card['price']} | 💳 القيمة: ${card['value']}\n"
                cards_text += f"   📅 تاريخ الحذف: {deleted_at}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("♻️ استعادة البطاقات", callback_data='restore_cards')],
                [InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, cards_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "✅ لا توجد بطاقات محذوفة", reply_markup)
    
    elif query.data == 'restore_cards':
        # Show deleted cards for restoration
        deleted_cards = await get_deleted_cards_for_admin()
        if deleted_cards:
            keyboard = []
            for card in deleted_cards[:20]:  # Limit to 20 cards
                country_info = COUNTRIES.get(card['country_code'], {})
                flag = country_info.get('flag', '🌍')
                card_text = f"♻️ {card['card_type']} - {flag} {card['country_code']} (${card['price']})"
                keyboard.append([InlineKeyboardButton(
                    card_text,
                    callback_data=f"restore_card_{card['card_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة للبطاقات المحذوفة", callback_data='view_deleted_cards')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                "♻️ استعادة البطاقات\n\nاختر البطاقة التي تريد استعادتها:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "✅ لا توجد بطاقات محذوفة للاستعادة", reply_markup        )
    
    # Handle black websites management
    elif query.data == 'manage_black_websites':
        keyboard = [
            [InlineKeyboardButton("➕ إضافة موقع", callback_data='add_black_website')],
            [InlineKeyboardButton("📝 تعديل موقع", callback_data='edit_black_websites')],
            [InlineKeyboardButton("🗑️ حذف موقع", callback_data='delete_black_websites')],
            [InlineKeyboardButton("📋 عرض المواقع", callback_data='view_black_websites')],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "🌐 إدارة المواقع السوداء\n\nاختر الإجراء المطلوب:",
            reply_markup
        )
    
    # Handle black websites actions
    elif query.data == 'add_black_website':
        # Start black website addition process
        context.user_data['adding_black_website'] = True
        context.user_data['black_website_step'] = 'url'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_black_websites')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "➕ إضافة موقع جديد\n\n1️⃣ ادخل رابط الموقع:",
            reply_markup
        )
    
    elif query.data == 'view_black_websites':
        # Show all black websites
        websites = await get_all_black_websites_for_admin()
        if websites:
            websites_text = "📋 جميع المواقع السوداء:\n\n"
            for website in websites[:10]:  # Show first 10 websites
                status = "✅ متاح" if website.get('is_available') else "❌ غير متاح"
                websites_text += f"🌐 {website['name']}\n"
                websites_text += f"🔗 {website['url']}\n"
                websites_text += f"💰 ${website['price']}\n"
                websites_text += f"📊 {status}\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, websites_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "📋 لا توجد مواقع في النظام حالياً", reply_markup)
    
    elif query.data == 'edit_black_websites':
        # Show websites for editing
        websites = await get_all_black_websites_for_admin()
        if websites:
            keyboard = []
            for website in websites[:20]:  # Limit to 20 websites
                status_icon = "✅" if website['is_available'] else "❌"
                keyboard.append([InlineKeyboardButton(
                    f"{status_icon} {website['name']} - ${website['price']}",
                    callback_data=f"edit_website_{website['website_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                "📝 تعديل المواقع\n\nاختر الموقع الذي تريد تعديله:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لا توجد مواقع للتعديل", reply_markup)
    
    elif query.data == 'delete_black_websites':
        # Show websites for deletion
        websites = await get_all_black_websites_for_admin()
        if websites:
            keyboard = []
            for website in websites[:20]:  # Limit to 20 websites
                status_icon = "✅" if website['is_available'] else "❌"
                keyboard.append([InlineKeyboardButton(
                    f"{status_icon} {website['name']} - ${website['price']}",
                    callback_data=f"delete_website_{website['website_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                "🗑️ حذف المواقع\n\n⚠️ تحذير: سيتم حذف الموقع نهائياً!\nاختر الموقع الذي تريد حذفه:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لا توجد مواقع للحذف", reply_markup)
    
    # Handle individual website actions
    elif query.data.startswith('edit_website_'):
        website_id = query.data[13:]  # Remove 'edit_website_' prefix
        website = await db_manager.get_black_website(website_id)
        
        if website:
            keyboard = [
                [InlineKeyboardButton("📝 تعديل الاسم", callback_data=f"edit_website_name_{website_id}")],
                [InlineKeyboardButton("🔗 تعديل الرابط", callback_data=f"edit_website_url_{website_id}")],
                [InlineKeyboardButton("💰 تعديل السعر", callback_data=f"edit_website_price_{website_id}")],
                [InlineKeyboardButton("📄 تعديل الوصف", callback_data=f"edit_website_desc_{website_id}")],
                [InlineKeyboardButton("🔙 العودة", callback_data='edit_black_websites')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            description = website.get('description', 'لا يوجد وصف')
            await safe_edit_message(
                query,
                f"📝 تعديل الموقع: {website['name']}\n\n"
                f"🔗 الرابط الحالي: {website['url']}\n"
                f"💰 السعر الحالي: ${website['price']}\n"
                f"📄 الوصف الحالي: {description}\n\n"
                f"اختر ما تريد تعديله:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data='edit_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لم يتم العثور على الموقع", reply_markup)
    
    elif query.data.startswith('edit_website_name_'):
        website_id = query.data[18:]  # Remove 'edit_website_name_' prefix
        context.user_data['editing_black_website'] = True
        context.user_data['editing_website_id'] = website_id
        context.user_data['editing_field'] = 'name'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"edit_website_{website_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "📝 تعديل اسم الموقع\n\nادخل الاسم الجديد:",
            reply_markup
        )
    
    elif query.data.startswith('edit_website_url_'):
        website_id = query.data[17:]  # Remove 'edit_website_url_' prefix
        context.user_data['editing_black_website'] = True
        context.user_data['editing_website_id'] = website_id
        context.user_data['editing_field'] = 'url'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"edit_website_{website_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "🔗 تعديل رابط الموقع\n\nادخل الرابط الجديد:",
            reply_markup
        )
    
    elif query.data.startswith('edit_website_price_'):
        website_id = query.data[19:]  # Remove 'edit_website_price_' prefix
        context.user_data['editing_black_website'] = True
        context.user_data['editing_website_id'] = website_id
        context.user_data['editing_field'] = 'price'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"edit_website_{website_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "💰 تعديل سعر الموقع\n\nادخل السعر الجديد (بالدولار):",
            reply_markup
        )
    
    elif query.data.startswith('edit_website_desc_'):
        website_id = query.data[18:]  # Remove 'edit_website_desc_' prefix
        context.user_data['editing_black_website'] = True
        context.user_data['editing_website_id'] = website_id
        context.user_data['editing_field'] = 'description'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"edit_website_{website_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "📄 تعديل وصف الموقع\n\nادخل الوصف الجديد:",
            reply_markup
        )
    
    elif query.data.startswith('delete_website_'):
        website_id = query.data[15:]  # Remove 'delete_website_' prefix
        website = await db_manager.get_black_website(website_id)
        
        if website:
            keyboard = [
                [InlineKeyboardButton("✅ نعم، احذف الموقع", callback_data=f"confirm_delete_website_{website_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data='delete_black_websites')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                f"⚠️ تأكيد حذف الموقع\n\n"
                f"🌐 الموقع: {website['name']}\n"
                f"🔗 الرابط: {website['url']}\n"
                f"💰 السعر: ${website['price']}\n\n"
                f"هل أنت متأكد من حذف هذا الموقع؟",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data='delete_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لم يتم العثور على الموقع", reply_markup)
    
    elif query.data.startswith('confirm_delete_website_'):
        website_id = query.data[23:]  # Remove 'confirm_delete_website_' prefix
        success = await db_manager.delete_black_website(website_id)
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "✅ تم حذف الموقع بنجاح!", reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data='delete_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ حدث خطأ في حذف الموقع", reply_markup)
    
    # Handle user management
    elif query.data == 'manage_users':
        keyboard = [
            [InlineKeyboardButton("📋 عرض المستخدمين", callback_data='list_users')],
            [InlineKeyboardButton("💰 شحن رصيد", callback_data='charge_balance')],
            [InlineKeyboardButton("🚫 حظر/إلغاء حظر", callback_data='block_users')],
            [InlineKeyboardButton("📊 إحصائيات المستخدمين", callback_data='user_stats')],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "👥 إدارة المستخدمين\n\nاختر العملية المطلوبة:",
            reply_markup
        )
    
    elif query.data == 'list_users':
        # Show users list
        users = await get_all_users_for_admin()
        if users:
            keyboard = []
            users_text = "👥 قائمة المستخدمين:\n\n"
            
            for i, user in enumerate(users[:15], 1):  # Show first 15 users
                username = user.get('username', 'غير محدد')
                first_name = user.get('first_name', 'غير محدد')
                balance = user.get('balance', 0.0)
                is_blocked = await db_manager.is_blacklisted(user['user_id'])
                
                status_icon = "🚫" if is_blocked else "👤"
                users_text += f"{i}. {status_icon} {first_name} (@{username}) | ${balance:.2f}\n"
                
                # Add button for each user
                keyboard.append([InlineKeyboardButton(
                    f"{status_icon} {first_name} (@{username})",
                    callback_data=f"user_{user['user_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔄 تحديث القائمة", callback_data='list_users')])
            keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(query, users_text, reply_markup)
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 تحديث القائمة", callback_data='list_users')],
                [InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "📭 لا يوجد مستخدمون مسجلون حالياً", reply_markup)
    
    elif query.data == 'charge_balance':
        # Show users for balance charging
        users = await get_all_users_for_admin()
        if users:
            keyboard = []
            for user in users[:20]:  # Show first 20 users
                username = user.get('username', 'غير محدد')
                first_name = user.get('first_name', 'غير محدد')
                balance = user.get('balance', 0.0)
                is_blocked = await db_manager.is_blacklisted(user['user_id'])
                
                if not is_blocked:  # Only show non-blocked users
                    user_text = f"💰 {first_name} (@{username}) - ${balance:.2f}"
                    keyboard.append([InlineKeyboardButton(
                        user_text,
                        callback_data=f"charge_user_{user['user_id']}"
                    )])
            
            if keyboard:
                keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await safe_edit_message(
                    query,
                    "💰 شحن رصيد المستخدمين\n\nاختر المستخدم لشحن رصيده:",
                    reply_markup
                )
            else:
                keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await safe_edit_message(query, "❌ لا يوجد مستخدمون نشطون لشحن رصيدهم", reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "📭 لا يوجد مستخدمون مسجلون", reply_markup)
    
    elif query.data == 'block_users':
        # Show users for blocking/unblocking
        users = await get_all_users_for_admin()
        if users:
            keyboard = []
            for user in users[:20]:  # Show first 20 users
                username = user.get('username', 'غير محدد')
                first_name = user.get('first_name', 'غير محدد')
                is_blocked = await db_manager.is_blacklisted(user['user_id'])
                
                status_icon = "🚫" if is_blocked else "👤"
                action_text = "إلغاء حظر" if is_blocked else "حظر"
                user_text = f"{status_icon} {first_name} (@{username}) - {action_text}"
                
                keyboard.append([InlineKeyboardButton(
                    user_text,
                    callback_data=f"toggle_block_{user['user_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                "🚫 حظر/إلغاء حظر المستخدمين\n\nاختر المستخدم لتغيير حالة الحظر:",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "📭 لا يوجد مستخدمون مسجلون", reply_markup)
    
    elif query.data == 'user_stats':
        # Show user statistics
        stats = await get_user_statistics()
        stats_text = f"""
📊 إحصائيات المستخدمين

👥 إجمالي المستخدمين: {stats['total_users']}
✅ المستخدمون النشطون: {stats['active_users']}
🚫 المستخدمون المحظورون: {stats['blocked_users']}
💰 إجمالي الأرصدة: ${stats['total_balance']:.2f}
📋 إجمالي الطلبات: {stats['total_orders']}
💵 إجمالي المبيعات: ${stats['total_sales']:.2f}

📅 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data='user_stats')],
            [InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(query, stats_text, reply_markup)
    
    # Handle individual user actions
    elif query.data.startswith('user_'):
        user_id = int(query.data[5:])  # Remove 'user_' prefix
        user_info = await db_manager.get_user(user_id)
        
        if user_info:
            is_blocked = await db_manager.is_blacklisted(user_id)
            username = user_info.get('username', 'غير محدد')
            first_name = user_info.get('first_name', 'غير محدد')
            last_name = user_info.get('last_name', 'غير محدد')
            balance = user_info.get('balance', 0.0)
            created_at = user_info.get('created_at', datetime.now(UTC))
            
            if isinstance(created_at, datetime):
                created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            else:
                created_str = 'غير محدد'
            
            status = "🚫 محظور" if is_blocked else "✅ نشط"
            
            user_details = f"""
👤 تفاصيل المستخدم

🆔 المعرف: {user_id}
👤 الاسم: {first_name} {last_name}
📱 اسم المستخدم: @{username}
💰 الرصيد: ${balance:.2f}
📊 الحالة: {status}
📅 تاريخ التسجيل: {created_str}

⚡ الإجراءات المتاحة:
            """
            
            keyboard = [
                [InlineKeyboardButton("💰 شحن رصيد", callback_data=f"charge_user_{user_id}")],
                [InlineKeyboardButton("🚫 حظر/إلغاء حظر", callback_data=f"toggle_block_{user_id}")],
                [InlineKeyboardButton("📋 عرض الطلبات", callback_data=f"user_orders_{user_id}")],
                [InlineKeyboardButton("💳 عرض المعاملات", callback_data=f"user_transactions_{user_id}")],
                [InlineKeyboardButton("🔙 العودة لقائمة المستخدمين", callback_data='list_users')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(query, user_details, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة المستخدمين", callback_data='list_users')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"❌ لم يتم العثور على المستخدم #{user_id}", reply_markup)
    
    # Handle balance charging
    elif query.data.startswith('charge_user_'):
        user_id = int(query.data[12:])  # Remove 'charge_user_' prefix
        context.user_data['charging_user'] = user_id
        
        user_info = await db_manager.get_user(user_id)
        if user_info:
            username = user_info.get('username', 'غير محدد')
            first_name = user_info.get('first_name', 'غير محدد')
            current_balance = user_info.get('balance', 0.0)
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f'user_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                f"💰 شحن رصيد المستخدم\n\n👤 المستخدم: {first_name} (@{username})\n💰 الرصيد الحالي: ${current_balance:.2f}\n\n💵 أدخل المبلغ المراد شحنه (مثال: 25.50):",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لشحن الرصيد", callback_data='charge_balance')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"❌ لم يتم العثور على المستخدم #{user_id}", reply_markup)
    
    # Handle user blocking/unblocking
    elif query.data.startswith('toggle_block_'):
        user_id = int(query.data[13:])  # Remove 'toggle_block_' prefix
        user_info = await db_manager.get_user(user_id)
        
        if user_info:
            is_blocked = await db_manager.is_blacklisted(user_id)
            username = user_info.get('username', 'غير محدد')
            first_name = user_info.get('first_name', 'غير محدد')
            
            action = "إلغاء حظر" if is_blocked else "حظر"
            action_verb = "إلغاء حظر" if is_blocked else "حظر"
            
            keyboard = [
                [InlineKeyboardButton(f"✅ نعم، {action_verb} المستخدم", callback_data=f"confirm_block_{user_id}_{not is_blocked}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data=f"user_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(
                query,
                f"⚠️ تأكيد {action} المستخدم\n\n👤 المستخدم: {first_name} (@{username})\n\nهل أنت متأكد من {action} هذا المستخدم؟",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لحظر المستخدمين", callback_data='block_users')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"❌ لم يتم العثور على المستخدم #{user_id}", reply_markup)
    
    elif query.data.startswith('confirm_block_'):
        parts = query.data.split('_')
        user_id = int(parts[2])
        should_block = parts[3] == 'True'
        
        success = await toggle_user_block_status(user_id, should_block)
        
        if success:
            action = "حظر" if should_block else "إلغاء حظر"
            keyboard = [[InlineKeyboardButton("🔙 العودة لحظر المستخدمين", callback_data='block_users')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                query,
                f"✅ تم {action} المستخدم بنجاح!\n\n📧 تم إشعار المستخدم بالتغيير.",
                reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لحظر المستخدمين", callback_data='block_users')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"❌ فشل في تغيير حالة المستخدم #{user_id}", reply_markup)
    
    # Handle user orders view
    elif query.data.startswith('user_orders_'):
        user_id = int(query.data[12:])  # Remove 'user_orders_' prefix
        orders = await get_user_orders(user_id)
        
        if orders:
            orders_text = f"📋 طلبات المستخدم #{user_id}:\n\n"
            for i, order in enumerate(orders[:10], 1):
                status_icon = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}.get(order['status'], "❓")
                orders_text += f"{i}. {status_icon} #{order['order_id'][:8]} - ${order['amount']:.2f}\n"
            
            keyboard = [[InlineKeyboardButton("🔙 العودة لتفاصيل المستخدم", callback_data=f'user_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, orders_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لتفاصيل المستخدم", callback_data=f'user_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"📭 لا توجد طلبات للمستخدم #{user_id}", reply_markup)
    
    elif query.data.startswith('user_transactions_'):
        user_id = int(query.data[18:])  # Remove 'user_transactions_' prefix
        transactions = await db_manager.get_user_transactions(user_id, 10)
        
        if transactions:
            trans_text = f"💳 معاملات المستخدم #{user_id}:\n\n"
            for i, trans in enumerate(transactions, 1):
                trans_type = trans.get('type', 'غير محدد')
                amount = trans.get('amount', 0.0)
                description = trans.get('description', 'غير محدد')
                created_at = trans.get('created_at', datetime.now(UTC))
                
                if isinstance(created_at, datetime):
                    date_str = created_at.strftime('%m-%d %H:%M')
                else:
                    date_str = 'غير محدد'
                
                trans_text += f"{i}. {trans_type} - ${amount:.2f} | {date_str}\n   {description}\n\n"
            
            keyboard = [[InlineKeyboardButton("🔙 العودة لتفاصيل المستخدم", callback_data=f'user_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, trans_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لتفاصيل المستخدم", callback_data=f'user_{user_id}')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, f"💳 لا توجد معاملات للمستخدم #{user_id}", reply_markup)
    
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
    
    # Handle individual card actions
    elif query.data.startswith('edit_card_'):
        card_id = query.data[10:]  # Remove 'edit_card_' prefix
        card = await get_card_by_id(card_id)
        
        if card:
            keyboard = [
                [InlineKeyboardButton("💰 تعديل السعر", callback_data=f"edit_price_{card_id}")],
                [InlineKeyboardButton("🏷️ تعديل النوع", callback_data=f"edit_type_{card_id}")],
                [InlineKeyboardButton("🔢 تعديل العدد المتاح", callback_data=f"edit_count_{card_id}")],
                [InlineKeyboardButton("🔙 العودة لقائمة التعديل", callback_data='edit_cards')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            available_count = card.get('number_of_available_cards', 0)
            status = f"متاحة ({available_count})" if card['is_available'] and available_count > 0 else "غير متاحة"
            country_info = COUNTRIES.get(card['country_code'], {})
            flag = country_info.get('flag', '🌍')
            
            card_details = f"""
📝 تعديل البطاقة

🆔 معرف البطاقة: {card['card_id']}
🏷️ النوع: {card['card_type']}
🌍 الدولة: {flag} {card['country_name']}
💰 السعر: ${card['price']}
💳 القيمة: ${card['value']}
🔢 العدد المتاح: {available_count}
📊 الحالة: {status}

اختر ما تريد تعديله:
            """
            
            await safe_edit_message(query, card_details, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة التعديل", callback_data='edit_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لم يتم العثور على البطاقة", reply_markup)
    
    elif query.data.startswith('remove_card_'):
        card_id = query.data[12:]  # Remove 'remove_card_' prefix
        card = await get_card_by_id(card_id)
        
        if card:
            keyboard = [
                [InlineKeyboardButton("✅ نعم، احذف البطاقة", callback_data=f"confirm_remove_{card_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data='remove_cards')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            country_info = COUNTRIES.get(card['country_code'], {})
            flag = country_info.get('flag', '🌍')
            
            confirmation_text = f"""
⚠️ تأكيد الحذف

هل أنت متأكد من حذف هذه البطاقة؟

🆔 معرف البطاقة: {card['card_id']}
🏷️ النوع: {card['card_type']}
🌍 الدولة: {flag} {card['country_name']}
💰 السعر: ${card['price']}
💳 القيمة: ${card['value']}

⚠️ تحذير: هذا الإجراء لا يمكن التراجع عنه!
            """
            
            await safe_edit_message(query, confirmation_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة الحذف", callback_data='remove_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ لم يتم العثور على البطاقة", reply_markup)
    
    elif query.data.startswith('toggle_card_'):
        card_id = query.data[12:]  # Remove 'toggle_card_' prefix
        success = await toggle_card_availability(card_id)
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة التفعيل", callback_data='toggle_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "✅ تم تغيير حالة البطاقة بنجاح!", reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة التفعيل", callback_data='toggle_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ فشل في تغيير حالة البطاقة", reply_markup)
    
    elif query.data.startswith('confirm_remove_') and not query.data.startswith('confirm_remove_group_'):
        card_id = query.data[15:]  # Remove 'confirm_remove_' prefix
        success = await remove_card_from_database(card_id)
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "✅ تم حذف البطاقة بنجاح!", reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة الحذف", callback_data='remove_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ فشل في حذف البطاقة", reply_markup)
    
    elif query.data.startswith('remove_group_'):
        # Parse callback data: remove_group_countrycode_cardtype_price
        parts = query.data.split('_', 3)  # Split into max 4 parts
        if len(parts) >= 4:
            country_code = parts[2]
            card_type = parts[3].rsplit('_', 1)[0].replace('_', ' ')  # Get card type, convert back from underscore format
            price = float(parts[3].rsplit('_', 1)[1])  # Get price from the last part
            
            # Get country info for display
            country_info = COUNTRIES.get(country_code, {})
            flag = country_info.get('flag', '🌍')
            country_name = country_info.get('name', country_code)
            
            # Get the count of cards in this group
            grouped_cards = await db_manager.get_grouped_cards_for_deletion()
            card_count = 0
            for group in grouped_cards:
                if (group['country_code'] == country_code and 
                    group['card_type'] == card_type and 
                    group['price'] == price):
                    card_count = group['count']
                    break
            
            keyboard = [
                [InlineKeyboardButton("✅ نعم، احذف جميع البطاقات", callback_data=f"confirm_remove_group_{country_code}_{card_type.replace(' ', '_')}_{price}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data='remove_cards')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            confirmation_text = f"""
⚠️ تأكيد حذف المجموعة

هل أنت متأكد من حذف جميع البطاقات في هذه المجموعة؟

🏷️ النوع: {card_type}
🌍 الدولة: {flag} {country_name}
💰 السعر: ${price}
📊 عدد البطاقات: {card_count}

⚠️ تحذير: سيتم حذف {card_count} بطاقة نهائياً!
هذا الإجراء لا يمكن التراجع عنه!
            """
            
            await safe_edit_message(query, confirmation_text, reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة الحذف", callback_data='remove_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ خطأ في معرف المجموعة", reply_markup)
    
    elif query.data.startswith('confirm_remove_group_'):
        # Parse callback data: confirm_remove_group_countrycode_cardtype_price
        parts = query.data.split('_', 4)  # Split into max 5 parts
        if len(parts) >= 5:
            country_code = parts[3]
            card_type = parts[4].rsplit('_', 1)[0].replace('_', ' ')  # Get card type, convert back from underscore format
            price = float(parts[4].rsplit('_', 1)[1])  # Get price from the last part
            
            # Perform bulk deletion
            deleted_count = await db_manager.bulk_delete_cards_by_group(country_code, card_type, price)
            
            if deleted_count > 0:
                keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await safe_edit_message(query, f"✅ تم حذف {deleted_count} بطاقة بنجاح!", reply_markup)
            else:
                keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة الحذف", callback_data='remove_cards')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await safe_edit_message(query, "❌ فشل في حذف البطاقات", reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لقائمة الحذف", callback_data='remove_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ خطأ في معرف المجموعة", reply_markup)
    
    elif query.data.startswith('restore_card_'):
        card_id = query.data[13:]  # Remove 'restore_card_' prefix
        success = await restore_card_from_deletion(card_id)
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 العودة للبطاقات المحذوفة", callback_data='view_deleted_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "✅ تم استعادة البطاقة بنجاح!", reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة للبطاقات المحذوفة", callback_data='view_deleted_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(query, "❌ فشل في استعادة البطاقة", reply_markup)
    
    # Handle card field editing
    elif query.data.startswith('edit_price_'):
        card_id = query.data[11:]  # Remove 'edit_price_' prefix
        context.user_data['editing_card'] = card_id
        context.user_data['edit_field'] = 'price'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f'edit_card_{card_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "💰 تعديل السعر\n\nأدخل السعر الجديد بالدولار (مثال: 25.00):",
            reply_markup
        )
    
    elif query.data.startswith('edit_type_'):
        card_id = query.data[10:]  # Remove 'edit_type_' prefix
        context.user_data['editing_card'] = card_id
        context.user_data['edit_field'] = 'card_type'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f'edit_card_{card_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "🏷️ تعديل نوع البطاقة\n\nأدخل نوع البطاقة الجديد (مثال: VISA 50$):",
            reply_markup
        )
    
    elif query.data.startswith('edit_count_'):
        card_id = query.data[11:]  # Remove 'edit_count_' prefix
        context.user_data['editing_card'] = card_id
        context.user_data['edit_field'] = 'number_of_available_cards'
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f'edit_card_{card_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_message(
            query,
            "🔢 تعديل العدد المتاح\n\nأدخل العدد الجديد للبطاقات المتاحة (مثال: 10):",
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
        
        # Clear only the specific context key we used
        context.user_data.pop('awaiting_card_image', None)
        
        # keyboard = [[InlineKeyboardButton("🏠 العودة للقائمة الرئيسية", callback_data='start')]]
        keyboard = []
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
    """Handle text input for adding new cards and editing cards"""
    user = update.effective_user
    
    # Check if user is admin
    admin_id = os.getenv('ADMIN_USER_ID')
    if not admin_id or str(user.id) != admin_id:
        return
    
    # Handle card editing
    if context.user_data.get('editing_card'):
        await handle_card_editing(update, context)
        return
    
    # Handle balance charging
    if context.user_data.get('charging_user'):
        await handle_balance_charging(update, context)
        return
    
    # Handle black website addition
    if context.user_data.get('adding_black_website'):
        await handle_black_website_addition_text(update, context)
        return
    
    # Handle black website editing
    if context.user_data.get('editing_black_website'):
        await handle_black_website_editing(update, context)
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
                context.user_data['value'] = price  # Set value equal to price
                context.user_data['card_step'] = 'quantity'  # Skip directly to quantity
                
                keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_cards')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ السعر: ${price}\n\n4️⃣ يرجى إدخال عدد البطاقات المطلوب إنشاؤها (مثال: 5):",
                    reply_markup=reply_markup
                )
            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح للسعر (مثال: 25.00)")
        
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
                    'is_deleted': False,
                    'created_at': datetime.now(UTC)
                }
                
                # Add multiple cards to database
                success_count = await add_bulk_cards_to_database(card_base_data, quantity)
                
                # Clear card addition context
                for key in ['adding_card', 'card_step', 'card_type', 'country_code', 'country_name', 'price', 'value']:
                    context.user_data.pop(key, None)
                
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
        # Clear card addition context on error
        for key in ['adding_card', 'card_step', 'card_type', 'country_code', 'country_name', 'price', 'value']:
            context.user_data.pop(key, None)
        await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة مرة أخرى.")


async def handle_card_editing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle card editing text input"""
    try:
        card_id = context.user_data['editing_card']
        field = context.user_data['edit_field']
        text = update.message.text
        
        success = False
        if field == 'price':
            try:
                price = float(text)
                success = await update_card_field(card_id, 'price', price)
            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح للسعر (مثال: 25.00)")
                return
        elif field == 'card_type':
            success = await update_card_field(card_id, 'card_type', text)
        elif field == 'number_of_available_cards':
            try:
                count = int(text)
                if count < 0:
                    await update.message.reply_text("❌ يرجى إدخال عدد أكبر من أو يساوي صفر")
                    return
                success = await update_card_field(card_id, 'number_of_available_cards', count)
                # Update availability status based on count
                if success:
                    await update_card_field(card_id, 'is_available', count > 0)
            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح للعدد (مثال: 10)")
                return
        
        # Clear editing context
        context.user_data.pop('editing_card', None)
        context.user_data.pop('edit_field', None)
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("✅ تم تحديث البطاقة بنجاح!", reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة البطاقات", callback_data='manage_cards')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("❌ فشل في تحديث البطاقة", reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error updating card: {e}")
        context.user_data.pop('editing_card', None)
        context.user_data.pop('edit_field', None)
        await update.message.reply_text("❌ حدث خطأ في تحديث البطاقة")


async def handle_balance_charging(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle balance charging text input"""
    try:
        user_id = context.user_data['charging_user']
        text = update.message.text
        
        try:
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text("❌ يرجى إدخال مبلغ أكبر من صفر")
                return
            
            if amount > 10000:
                await update.message.reply_text("❌ المبلغ كبير جداً. الحد الأقصى هو $10,000")
                return
            
            # Charge user balance
            success = await charge_user_balance(user_id, amount)
            
            # Clear charging context
            context.user_data.pop('charging_user', None)
            
            if success:
                user_info = await db_manager.get_user(user_id)
                username = user_info.get('username', 'غير محدد') if user_info else 'غير محدد'
                first_name = user_info.get('first_name', 'غير محدد') if user_info else 'غير محدد'
                new_balance = await db_manager.get_user_balance(user_id)
                
                keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المستخدمين", callback_data='manage_users')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                success_text = f"""
✅ تم شحن الرصيد بنجاح!

👤 المستخدم: {first_name} (@{username})
💰 المبلغ المشحون: ${amount:.2f}
💳 الرصيد الجديد: ${new_balance:.2f}

📧 تم إشعار المستخدم بالشحن
                """
                
                await update.message.reply_text(success_text, reply_markup=reply_markup)
            else:
                keyboard = [[InlineKeyboardButton("🔙 العودة لشحن الرصيد", callback_data='charge_balance')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("❌ فشل في شحن الرصيد", reply_markup=reply_markup)
                
        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال رقم صحيح (مثال: 25.50)")
            
    except Exception as e:
        logger.error(f"Error handling balance charging: {e}")
        context.user_data.pop('charging_user', None)
        await update.message.reply_text("❌ حدث خطأ في شحن الرصيد")


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
    """Get all cards for admin view (excluding deleted cards)"""
    try:
        # Get all cards from database (excluding deleted ones)
        cursor = db_manager.cards.find({
            "is_deleted": {"$ne": True}  # Exclude deleted cards
        }).sort("created_at", -1)
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
    """Add a single card with specified quantity to the database"""
    try:
        # First, ensure the country exists in the countries collection
        await ensure_country_exists(card_base_data['country_code'], card_base_data['country_name'])
        
        # Create unique card ID
        base_pattern = f"{card_base_data['country_code']}_{card_base_data['card_type'].replace(' ', '_')}_{int(card_base_data['value'])}"
        
        # Check if a card with this exact specification already exists
        existing_card = await db_manager.cards.find_one({
            "country_code": card_base_data['country_code'],
            "card_type": card_base_data['card_type'],
            "price": card_base_data['price'],
            "value": card_base_data['value'],
            "is_deleted": {"$ne": True}
        })
        
        if existing_card:
            # If card exists, increment the available count
            result = await db_manager.cards.update_one(
                {"card_id": existing_card['card_id']},
                {
                    "$inc": {"number_of_available_cards": quantity},
                    "$set": {
                        "is_available": True,
                        "updated_at": datetime.now(UTC)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated existing card {existing_card['card_id']} with {quantity} additional units")
                return quantity
            else:
                logger.error(f"Failed to update existing card {existing_card['card_id']}")
                return 0
        else:
            # Create new card with the specified quantity
            card_id = f"{base_pattern}_{int(datetime.now(UTC).timestamp())}"
            card_data = card_base_data.copy()
            card_data['card_id'] = card_id
            card_data['number_of_available_cards'] = quantity
            
            try:
                # Insert card into database
                result = await db_manager.cards.insert_one(card_data)
                
                if result.inserted_id:
                    logger.info(f"Added new card {card_id} with {quantity} units")
                    return quantity
                else:
                    logger.error(f"Failed to add new card {card_id}")
                    return 0
            except Exception as insert_error:
                logger.error(f"Error inserting card {card_id}: {insert_error}")
                return 0
        
    except Exception as e:
        logger.error(f"Error adding card to database: {e}")
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
                "created_at": datetime.now(UTC)
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


async def get_card_by_id(card_id):
    """Get a single card by its ID"""
    try:
        card = await db_manager.cards.find_one({"card_id": card_id})
        return card
    except Exception as e:
        logger.error(f"Error getting card by ID {card_id}: {e}")
        return None


async def update_card_field(card_id, field, value):
    """Update a specific field of a card"""
    try:
        result = await db_manager.cards.update_one(
            {"card_id": card_id},
            {"$set": {field: value, "updated_at": datetime.now(UTC)}}
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated card {card_id}: {field} = {value}")
            return True
        else:
            logger.error(f"Failed to update card {card_id}: {field} = {value}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating card field: {e}")
        return False


async def toggle_card_availability(card_id):
    """Toggle the availability status of a card"""
    try:
        # Get current status
        card = await db_manager.cards.find_one({"card_id": card_id})
        if not card:
            return False
        
        new_status = not card['is_available']
        
        result = await db_manager.cards.update_one(
            {"card_id": card_id},
            {"$set": {"is_available": new_status, "updated_at": datetime.now(UTC)}}
        )
        
        if result.modified_count > 0:
            status_text = "متاحة" if new_status else "غير متاحة"
            logger.info(f"Toggled card {card_id} availability to: {status_text}")
            return True
        else:
            logger.error(f"Failed to toggle card {card_id} availability")
            return False
            
    except Exception as e:
        logger.error(f"Error toggling card availability: {e}")
        return False


async def remove_card_from_database(card_id):
    """Soft delete a card from the database"""
    try:
        result = await db_manager.cards.update_one(
            {"card_id": card_id},
            {
                "$set": {
                    "is_deleted": True,
                    "is_available": False,  # Also mark as unavailable
                    "deleted_at": datetime.now(UTC)
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Soft deleted card: {card_id}")
            return True
        else:
            logger.error(f"Failed to soft delete card: {card_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error soft deleting card from database: {e}")
        return False


async def get_deleted_cards_for_admin():
    """Get all deleted cards for admin view"""
    try:
        cursor = db_manager.cards.find({
            "is_deleted": True  # Only deleted cards
        }).sort("deleted_at", -1)
        cards = await cursor.to_list(length=None)
        return cards
    except Exception as e:
        logger.error(f"Error getting deleted cards for admin: {e}")
        return []


async def restore_card_from_deletion(card_id):
    """Restore a soft-deleted card"""
    try:
        result = await db_manager.cards.update_one(
            {"card_id": card_id, "is_deleted": True},
            {
                "$set": {
                    "is_deleted": False,
                    "is_available": True,  # Restore as available
                    "restored_at": datetime.now(UTC)
                },
                "$unset": {
                    "deleted_at": ""  # Remove deleted_at field
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Restored card: {card_id}")
            return True
        else:
            logger.error(f"Failed to restore card: {card_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error restoring card from deletion: {e}")
        return False


# Black websites management functions
async def get_all_black_websites_for_admin():
    """Get all black websites for admin view"""
    try:
        websites = await db_manager.get_all_black_websites()
        return websites
    except Exception as e:
        logger.error(f"Error getting black websites for admin: {e}")
        return []


async def handle_black_website_addition_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input for adding new black websites"""
    user = update.effective_user
    
    # Check if user is admin
    admin_id = os.getenv('ADMIN_USER_ID')
    if not admin_id or str(user.id) != admin_id:
        return
    
    # Check if we're adding a black website
    if not context.user_data.get('adding_black_website'):
        return
    
    step = context.user_data.get('black_website_step')
    text = update.message.text
    
    try:
        if step == 'url':
            context.user_data['website_url'] = text
            context.user_data['black_website_step'] = 'name'
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"✅ رابط الموقع: {text}\n\n2️⃣ ادخل اسم الموقع:",
                reply_markup=reply_markup
            )
        
        elif step == 'name':
            context.user_data['website_name'] = text
            context.user_data['black_website_step'] = 'price'
            
            keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"✅ اسم الموقع: {text}\n\n3️⃣ ادخل سعر الشراء (بالدولار):",
                reply_markup=reply_markup
            )
        
        elif step == 'price':
            try:
                price = float(text)
                context.user_data['website_price'] = price
                context.user_data['black_website_step'] = 'description'
                
                keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data='manage_black_websites')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ السعر: ${price}\n\n4️⃣ ادخل وصف الموقع (سيتم إرساله مع الرابط للعميل):",
                    reply_markup=reply_markup
                )
            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح للسعر (مثال: 25.00)")
        
        elif step == 'description':
            # Create the black website
            success = await db_manager.create_black_website(
                name=context.user_data['website_name'],
                url=context.user_data['website_url'],
                price=context.user_data['website_price'],
                description=text
            )
            
            if success:
                keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"✅ تم إضافة الموقع بنجاح!\n\n"
                    f"🌐 الاسم: {context.user_data['website_name']}\n"
                    f"🔗 الرابط: {context.user_data['website_url']}\n"
                    f"💰 السعر: ${context.user_data['website_price']}\n"
                    f"📝 الوصف: {text}",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ حدث خطأ في إضافة الموقع. يرجى المحاولة مرة أخرى.")
            
            # Clear user data
            context.user_data.pop('adding_black_website', None)
            context.user_data.pop('black_website_step', None)
            context.user_data.pop('website_name', None)
            context.user_data.pop('website_url', None)
            context.user_data.pop('website_price', None)
        
    except Exception as e:
        logger.error(f"Error in black website addition: {e}")
        await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة مرة أخرى.")


async def handle_black_website_editing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input for editing black websites"""
    user = update.effective_user
    
    # Check if user is admin
    admin_id = os.getenv('ADMIN_USER_ID')
    if not admin_id or str(user.id) != admin_id:
        return
    
    # Check if we're editing a black website
    if not context.user_data.get('editing_black_website'):
        return
    
    website_id = context.user_data.get('editing_website_id')
    field = context.user_data.get('editing_field')
    text = update.message.text
    
    try:
        if field == 'name':
            success = await db_manager.update_black_website(website_id, name=text)
        elif field == 'url':
            success = await db_manager.update_black_website(website_id, url=text)
        elif field == 'price':
            try:
                price = float(text)
                success = await db_manager.update_black_website(website_id, price=price)
            except ValueError:
                await update.message.reply_text("❌ يرجى إدخال رقم صحيح للسعر")
                return
        elif field == 'description':
            success = await db_manager.update_black_website(website_id, description=text)
        else:
            success = False
        
        if success:
            keyboard = [[InlineKeyboardButton("🔙 العودة لإدارة المواقع", callback_data='manage_black_websites')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"✅ تم تحديث {field} بنجاح!",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ حدث خطأ في التحديث. يرجى المحاولة مرة أخرى.")
        
        # Clear editing state
        context.user_data.pop('editing_black_website', None)
        context.user_data.pop('editing_website_id', None)
        context.user_data.pop('editing_field', None)
        
    except Exception as e:
        logger.error(f"Error in black website editing: {e}")
        await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة مرة أخرى.")


async def complete_order(order_id):
    """Mark an order as completed and notify the customer"""
    try:
        # Update order status to completed
        result = await db_manager.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.now(UTC)
                }
            }
        )
        
        if result.modified_count > 0:
            # Get order details for notification
            order = await db_manager.get_order_by_id(order_id)
            if order:
                # Create notification for customer
                notification_data = {
                    "user_id": order['user_id'],
                    "order_id": order_id,
                    "message": f"✅ تم إكمال طلبك #{order_id} بنجاح!\n\n🎉 شكراً لك على استخدام خدماتنا."
                }
                
                await db_manager.create_notification("order_completed", notification_data)
                logger.info(f"Order {order_id} marked as completed")
                return True
        
        logger.error(f"Failed to complete order {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error completing order {order_id}: {e}")
        return False


async def cancel_order(order_id):
    """Cancel an order and notify the customer"""
    try:
        # Update order status to cancelled
        result = await db_manager.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.now(UTC)
                }
            }
        )
        
        if result.modified_count > 0:
            # Get order details for notification
            order = await db_manager.get_order_by_id(order_id)
            if order:
                # Create notification for customer
                notification_data = {
                    "user_id": order['user_id'],
                    "order_id": order_id,
                    "message": f"❌ تم إلغاء طلبك #{order_id}\n\n💬 إذا كان لديك أي استفسار، يرجى التواصل مع الدعم."
                }
                
                await db_manager.create_notification("order_cancelled", notification_data)
                logger.info(f"Order {order_id} cancelled")
                return True
        
        logger.error(f"Failed to cancel order {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        return False


async def get_all_users_for_admin():
    """Get all users for admin management"""
    try:
        cursor = db_manager.users.find({}).sort("created_at", -1)
        users = await cursor.to_list(length=None)
        return users
    except Exception as e:
        logger.error(f"Error getting users for admin: {e}")
        return []


async def get_user_statistics():
    """Get user statistics for admin dashboard"""
    try:
        total_users = await db_manager.users.count_documents({})
        blocked_users = await db_manager.blacklist.count_documents({})
        active_users = total_users - blocked_users
        
        # Calculate total balance
        pipeline = [
            {"$group": {"_id": None, "total_balance": {"$sum": "$balance"}}}
        ]
        balance_result = await db_manager.users.aggregate(pipeline).to_list(1)
        total_balance = balance_result[0]['total_balance'] if balance_result else 0.0
        
        # Get order statistics
        total_orders = await db_manager.orders.count_documents({})
        
        # Calculate total sales (completed orders)
        sales_pipeline = [
            {"$match": {"status": "completed"}},
            {"$group": {"_id": None, "total_sales": {"$sum": "$amount"}}}
        ]
        sales_result = await db_manager.orders.aggregate(sales_pipeline).to_list(1)
        total_sales = sales_result[0]['total_sales'] if sales_result else 0.0
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
            'total_balance': total_balance,
            'total_orders': total_orders,
            'total_sales': total_sales
        }
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        return {
            'total_users': 0,
            'active_users': 0,
            'blocked_users': 0,
            'total_balance': 0.0,
            'total_orders': 0,
            'total_sales': 0.0
        }


async def get_user_orders(user_id):
    """Get orders for a specific user"""
    try:
        cursor = db_manager.orders.find({"user_id": user_id}).sort("created_at", -1)
        orders = await cursor.to_list(length=None)
        return orders
    except Exception as e:
        logger.error(f"Error getting orders for user {user_id}: {e}")
        return []


async def charge_user_balance(user_id, amount):
    """Charge user balance and create notification"""
    try:
        # Update user balance
        success = await db_manager.update_user_balance(user_id, amount)
        
        if success:
            # Create transaction record
            await db_manager.create_transaction(
                user_id=user_id,
                transaction_type="admin_charge",
                amount=amount,
                description=f"شحن رصيد من الإدارة: ${amount:.2f}"
            )
            
            # Get updated balance
            new_balance = await db_manager.get_user_balance(user_id)
            
            # Create notification for customer
            notification_data = {
                "user_id": user_id,
                "amount": amount,
                "new_balance": new_balance,
                "message": f"💰 تم شحن رصيدك بمبلغ ${amount:.2f}\n\n💳 رصيدك الحالي: ${new_balance:.2f}\n\n🎉 يمكنك الآن شراء البطاقات!"
            }
            
            await db_manager.create_notification("balance_updated", notification_data)
            logger.info(f"Charged user {user_id} with ${amount:.2f}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error charging user {user_id} balance: {e}")
        return False


async def toggle_user_block_status(user_id, should_block):
    """Block or unblock a user and create notification"""
    try:
        if should_block:
            # Block user
            success = await db_manager.add_to_blacklist(user_id, "حظر من الإدارة")
            action = "حظر"
            message = "🚫 تم حظرك من استخدام البوت\n\n💬 للاستفسار، يرجى التواصل مع الدعم."
        else:
            # Unblock user
            success = await db_manager.remove_from_blacklist(user_id)
            action = "إلغاء حظر"
            message = "✅ تم إلغاء حظرك من البوت\n\n🎉 يمكنك الآن استخدام جميع الخدمات!"
        
        if success:
            # Create notification for customer
            notification_data = {
                "user_id": user_id,
                "message": message,
                "action": action
            }
            
            notification_type = "user_unblocked" if not should_block else "user_blocked"
            await db_manager.create_notification(notification_type, notification_data)
            logger.info(f"User {user_id} {action} successfully")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error toggling user {user_id} block status: {e}")
        return False


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
    
    # Get webhook configuration
    WEBHOOK_URL = os.getenv('ORDER_WEBHOOK_URL')
    WEBHOOK_PORT = int(os.getenv('ORDER_WEBHOOK_PORT', '8444'))
    USE_WEBHOOKS = os.getenv('USE_WEBHOOKS', 'false').lower() == 'true'
    
    if USE_WEBHOOKS and WEBHOOK_URL:
        # Run with webhooks
        logging.info(f"Starting order management bot with webhooks on port {WEBHOOK_PORT}...")
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
        logging.info("Starting order management bot with polling...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            poll_interval=3.0,  # Check every 3 seconds (admin bot can be slower)
            timeout=10          # Wait up to 10 seconds for updates
        )


if __name__ == '__main__':
    main()
