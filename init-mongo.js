// MongoDB initialization script
db = db.getSiblingDB('telegram_bot');

// Create collections
db.createCollection('users');
db.createCollection('cards');
db.createCollection('transactions');
db.createCollection('blacklist');

// Create indexes for better performance
db.users.createIndex({ "user_id": 1 }, { unique: true });
db.users.createIndex({ "username": 1 });
db.cards.createIndex({ "card_id": 1 }, { unique: true });
db.transactions.createIndex({ "user_id": 1 });
db.transactions.createIndex({ "timestamp": 1 });
db.blacklist.createIndex({ "user_id": 1 }, { unique: true });

// Insert sample data
db.users.insertMany([
    {
        user_id: 123456789,
        username: "sample_user",
        first_name: "Sample",
        last_name: "User",
        balance: 0.0,
        created_at: new Date(),
        is_active: true
    }
]);

db.cards.insertMany([
    {
        card_id: "CARD001",
        card_type: "VISA",
        value: 50.0,
        currency: "USD",
        is_available: true,
        created_at: new Date()
    },
    {
        card_id: "CARD002", 
        card_type: "MASTERCARD",
        value: 100.0,
        currency: "USD",
        is_available: true,
        created_at: new Date()
    }
]);

print('Database initialized successfully!');
