"""
Database configuration and operations for the Telegram bot
"""
import os
import logging
from datetime import datetime, UTC
from typing import Optional, Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, PyMongoError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB database manager for the Telegram bot"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.users: Optional[AsyncIOMotorCollection] = None
        self.cards: Optional[AsyncIOMotorCollection] = None
        self.transactions: Optional[AsyncIOMotorCollection] = None
        self.blacklist: Optional[AsyncIOMotorCollection] = None
        self.countries: Optional[AsyncIOMotorCollection] = None
        self.orders: Optional[AsyncIOMotorCollection] = None
        self.notifications: Optional[AsyncIOMotorCollection] = None
        self.black_websites: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self, mongodb_url: str = None):
        """Connect to MongoDB database"""
        try:
            if not mongodb_url:
                mongodb_url = os.getenv('MONGODB_URL', 'mongodb://admin:password123@localhost:27017/telegram_bot?authSource=admin')
            
            self.client = AsyncIOMotorClient(mongodb_url)
            self.db = self.client.telegram_bot
            
            # Initialize collections
            self.users = self.db.users
            self.cards = self.db.cards
            self.transactions = self.db.transactions
            self.blacklist = self.db.blacklist
            self.countries = self.db.countries
            self.orders = self.db.orders
            self.notifications = self.db.notifications
            self.black_websites = self.db.black_websites
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    # User operations
    async def create_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Create a new user"""
        try:
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "balance": 0.0,
                "created_at": datetime.now(UTC),
                "is_active": True
            }
            await self.users.insert_one(user_data)
            logger.info(f"Created new user: {user_id}")
            return True
        except DuplicateKeyError:
            logger.info(f"User {user_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            user = await self.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def update_user_balance(self, user_id: int, amount: float) -> bool:
        """Update user balance"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": amount}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating balance for user {user_id}: {e}")
            return False
    
    async def get_user_balance(self, user_id: int) -> float:
        """Get user balance"""
        user = await self.get_user(user_id)
        return user.get("balance", 0.0) if user else 0.0
    
    # Card operations
    async def get_available_cards(self) -> List[Dict[str, Any]]:
        """Get all available cards"""
        try:
            cards = await self.cards.find({"is_available": True}).to_list(length=None)
            return cards
        except Exception as e:
            logger.error(f"Error getting available cards: {e}")
            return []
    
    async def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get card by ID"""
        try:
            card = await self.cards.find_one({"card_id": card_id})
            return card
        except Exception as e:
            logger.error(f"Error getting card {card_id}: {e}")
            return None
    
    async def reserve_card(self, card_id: str, user_id: int) -> bool:
        """Reserve a card for a user"""
        try:
            result = await self.cards.update_one(
                {"card_id": card_id, "is_available": True},
                {
                    "$set": {
                        "is_available": False,
                        "reserved_by": user_id,
                        "reserved_at": datetime.now(UTC)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error reserving card {card_id}: {e}")
            return False
    
    # Transaction operations
    async def create_transaction(self, user_id: int, transaction_type: str, amount: float, description: str = None) -> bool:
        """Create a new transaction"""
        try:
            transaction_data = {
                "user_id": user_id,
                "type": transaction_type,  # 'deposit', 'withdrawal', 'card_purchase'
                "amount": amount,
                "description": description,
                "timestamp": datetime.now(UTC),
                "status": "completed"
            }
            await self.transactions.insert_one(transaction_data)
            logger.info(f"Created transaction for user {user_id}: {transaction_type} {amount}")
            return True
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return False
    
    async def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user transactions"""
        try:
            transactions = await self.transactions.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit).to_list(length=None)
            return transactions
        except Exception as e:
            logger.error(f"Error getting transactions for user {user_id}: {e}")
            return []
    
    # Blacklist operations
    async def add_to_blacklist(self, user_id: int, reason: str = None) -> bool:
        """Add user to blacklist"""
        try:
            blacklist_data = {
                "user_id": user_id,
                "reason": reason,
                "added_at": datetime.now(UTC)
            }
            await self.blacklist.insert_one(blacklist_data)
            logger.info(f"Added user {user_id} to blacklist")
            return True
        except DuplicateKeyError:
            logger.info(f"User {user_id} already in blacklist")
            return False
        except Exception as e:
            logger.error(f"Error adding user {user_id} to blacklist: {e}")
            return False
    
    async def is_blacklisted(self, user_id: int) -> bool:
        """Check if user is blacklisted"""
        try:
            result = await self.blacklist.find_one({"user_id": user_id})
            return result is not None
        except Exception as e:
            logger.error(f"Error checking blacklist for user {user_id}: {e}")
            return False
    
    async def remove_from_blacklist(self, user_id: int) -> bool:
        """Remove user from blacklist"""
        try:
            result = await self.blacklist.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error removing user {user_id} from blacklist: {e}")
            return False
    
    # Countries operations
    async def get_available_countries(self) -> List[Dict[str, Any]]:
        """Get all available countries"""
        try:
            countries = await self.countries.find({"is_active": True}).sort("name", 1).to_list(length=None)
            return countries
        except Exception as e:
            logger.error(f"Error getting available countries: {e}")
            return []
    
    async def get_cards_by_country(self, country_code: str) -> List[Dict[str, Any]]:
        """Get available cards for a specific country"""
        try:
            cards = await self.cards.find({
                "country_code": country_code,
                "is_available": True,
                "is_deleted": {"$ne": True}  # Exclude deleted cards
            }).to_list(length=None)
            return cards
        except Exception as e:
            logger.error(f"Error getting cards for country {country_code}: {e}")
            return []
    
    async def get_grouped_cards_by_country(self, country_code: str) -> List[Dict[str, Any]]:
        """Get available cards grouped by type and price for a specific country"""
        try:
            pipeline = [
                {
                    "$match": {
                        "country_code": country_code,
                        "is_available": True,
                        "is_deleted": {"$ne": True}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "card_type": "$card_type",
                            "price": "$price",
                            "value": "$value",
                            "country_code": "$country_code",
                            "country_name": "$country_name"
                        },
                        "count": {"$sum": 1},
                        "card_ids": {"$push": "$card_id"}  # Keep track of individual card IDs
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "card_type": "$_id.card_type",
                        "price": "$_id.price",
                        "value": "$_id.value",
                        "country_code": "$_id.country_code",
                        "country_name": "$_id.country_name",
                        "count": 1,
                        "card_ids": 1
                    }
                },
                {
                    "$sort": {"price": 1, "card_type": 1}  # Sort by price then by type
                }
            ]
            
            cursor = self.cards.aggregate(pipeline)
            grouped_cards = await cursor.to_list(length=None)
            return grouped_cards
        except Exception as e:
            logger.error(f"Error getting grouped cards for country {country_code}: {e}")
            return []
    
    async def get_available_card_from_group(self, country_code: str, card_type: str, price: float) -> Optional[Dict[str, Any]]:
        """Get one available card from a specific group (type + price)"""
        try:
            card = await self.cards.find_one({
                "country_code": country_code,
                "card_type": card_type,
                "price": price,
                "is_available": True,
                "is_deleted": {"$ne": True}
            })
            return card
        except Exception as e:
            logger.error(f"Error getting available card from group {card_type} {price}: {e}")
            return None
    
    # Orders operations
    async def create_order(self, user_id: int, card_id: str, country_code: str, amount: float) -> Optional[str]:
        """Create a new order"""
        try:
            from bson import ObjectId
            order_id = str(ObjectId())
            
            order_data = {
                "_id": ObjectId(order_id),
                "order_id": order_id,
                "user_id": user_id,
                "card_id": card_id,
                "country_code": country_code,
                "amount": amount,
                "status": "pending",  # pending, confirmed, completed, cancelled
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            }
            
            await self.orders.insert_one(order_data)
            logger.info(f"Created order {order_id} for user {user_id}")
            return order_id
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        try:
            from bson import ObjectId
            order = await self.orders.find_one({"_id": ObjectId(order_id)})
            return order
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        try:
            from bson import ObjectId
            result = await self.orders.update_one(
                {"_id": ObjectId(order_id)},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now(UTC)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return False
    
    async def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get all pending orders"""
        try:
            cursor = self.orders.find({"status": "pending"}).sort("created_at", -1)
            orders = await cursor.to_list(length=None)
            return orders
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            return []
    
    async def get_completed_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get completed orders"""
        try:
            cursor = self.orders.find({"status": "completed"}).sort("created_at", -1).limit(limit)
            orders = await cursor.to_list(length=None)
            return orders
        except Exception as e:
            logger.error(f"Error getting completed orders: {e}")
            return []
    
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        try:
            order = await self.orders.find_one({"order_id": order_id})
            return order
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    async def create_notification(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Create a notification for the order bot to process"""
        try:
            notification_id = f"notif_{int(datetime.now(UTC).timestamp() * 1000)}"
            notification = {
                "notification_id": notification_id,
                "type": notification_type,
                "data": data,
                "status": "pending",
                "created_at": datetime.now(UTC),
                "processed_at": None
            }
            
            await self.notifications.insert_one(notification)
            logger.info(f"Created notification {notification_id} of type {notification_type}")
            return notification_id
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    async def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get all pending notifications"""
        try:
            cursor = self.notifications.find({"status": "pending"}).sort("created_at", 1)
            notifications = await cursor.to_list(length=None)
            return notifications
        except Exception as e:
            logger.error(f"Error getting pending notifications: {e}")
            return []
    
    async def mark_notification_processed(self, notification_id: str) -> bool:
        """Mark a notification as processed"""
        try:
            result = await self.notifications.update_one(
                {"notification_id": notification_id},
                {
                    "$set": {
                        "status": "processed",
                        "processed_at": datetime.now(UTC)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as processed: {e}")
            return False
    
    # Black websites operations
    async def create_black_website(self, name: str, url: str, price: float, description: str = "") -> bool:
        """Create a new black website"""
        try:
            website_data = {
                "website_id": f"bw_{int(datetime.now(UTC).timestamp())}",
                "name": name,
                "url": url,
                "price": price,
                "description": description,
                "is_available": True,
                "is_deleted": False,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            }
            result = await self.black_websites.insert_one(website_data)
            logger.info(f"Created black website: {name}")
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error creating black website {name}: {e}")
            return False
    
    async def get_available_black_websites(self) -> List[Dict[str, Any]]:
        """Get all available black websites"""
        try:
            cursor = self.black_websites.find({
                "is_available": True,
                "is_deleted": {"$ne": True}
            }).sort("name", 1)
            websites = await cursor.to_list(length=None)
            return websites
        except Exception as e:
            logger.error(f"Error getting available black websites: {e}")
            return []
    
    async def get_all_black_websites(self) -> List[Dict[str, Any]]:
        """Get all black websites for admin (excluding deleted)"""
        try:
            cursor = self.black_websites.find({
                "is_deleted": {"$ne": True}
            }).sort("created_at", -1)
            websites = await cursor.to_list(length=None)
            return websites
        except Exception as e:
            logger.error(f"Error getting all black websites: {e}")
            return []
    
    async def get_black_website(self, website_id: str) -> Optional[Dict[str, Any]]:
        """Get black website by ID"""
        try:
            website = await self.black_websites.find_one({"website_id": website_id})
            return website
        except Exception as e:
            logger.error(f"Error getting black website {website_id}: {e}")
            return None
    
    async def update_black_website(self, website_id: str, name: str = None, url: str = None, price: float = None, description: str = None) -> bool:
        """Update black website details"""
        try:
            update_data = {"updated_at": datetime.now(UTC)}
            if name is not None:
                update_data["name"] = name
            if url is not None:
                update_data["url"] = url
            if price is not None:
                update_data["price"] = price
            if description is not None:
                update_data["description"] = description
            
            result = await self.black_websites.update_one(
                {"website_id": website_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating black website {website_id}: {e}")
            return False
    
    async def delete_black_website(self, website_id: str) -> bool:
        """Soft delete black website"""
        try:
            result = await self.black_websites.update_one(
                {"website_id": website_id},
                {
                    "$set": {
                        "is_deleted": True,
                        "is_available": False,
                        "updated_at": datetime.now(UTC)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deleting black website {website_id}: {e}")
            return False
    
    async def purchase_black_website(self, website_id: str, user_id: int) -> bool:
        """Mark black website as purchased (unavailable)"""
        try:
            result = await self.black_websites.update_one(
                {"website_id": website_id, "is_available": True},
                {
                    "$set": {
                        "is_available": True,
                        "purchased_by": user_id,
                        "purchased_at": datetime.now(UTC),
                        "updated_at": datetime.now(UTC)
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error purchasing black website {website_id}: {e}")
            return False

# Global database instance
db_manager = DatabaseManager()
