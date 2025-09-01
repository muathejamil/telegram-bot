import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
            [InlineKeyboardButton("📝 تعديل البطاقات", callback_data='edit_cards')],
            [InlineKeyboardButton("🗑️ حذف البطاقات", callback_data='delete_cards')],
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
        await db_manager.update_order_status(order_id, 'completed')
        await safe_edit_message(query, f"✅ تم تأكيد إرسال البطاقة للطلب #{order_id}")
    
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
    
    # Run the bot until the user presses Ctrl-C
    logging.info("Starting order management bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
