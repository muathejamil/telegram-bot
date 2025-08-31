"""
Database configuration and operations for the Telegram bot
"""
import os
import logging
from datetime import datetime
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
                "created_at": datetime.utcnow(),
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
                        "reserved_at": datetime.utcnow()
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
                "timestamp": datetime.utcnow(),
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
                "added_at": datetime.utcnow()
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
                "is_available": True
            }).to_list(length=None)
            return cards
        except Exception as e:
            logger.error(f"Error getting cards for country {country_code}: {e}")
            return []
    
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
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
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
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return False

# Global database instance
db_manager = DatabaseManager()
