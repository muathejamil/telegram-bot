// MongoDB initialization script
db = db.getSiblingDB('telegram_bot');

// Create collections
db.createCollection('users');
db.createCollection('cards');
db.createCollection('transactions');
db.createCollection('blacklist');
db.createCollection('countries');
db.createCollection('orders');

// Create indexes for better performance
db.users.createIndex({ "user_id": 1 }, { unique: true });
db.users.createIndex({ "username": 1 });
db.cards.createIndex({ "card_id": 1 }, { unique: true });
db.cards.createIndex({ "country_code": 1 });
db.cards.createIndex({ "is_available": 1 });
db.transactions.createIndex({ "user_id": 1 });
db.transactions.createIndex({ "timestamp": 1 });
db.blacklist.createIndex({ "user_id": 1 }, { unique: true });
db.countries.createIndex({ "code": 1 }, { unique: true });
db.orders.createIndex({ "user_id": 1 });
db.orders.createIndex({ "status": 1 });
db.orders.createIndex({ "created_at": 1 });

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

// Insert sample countries
db.countries.insertMany([
    {
        code: "US",
        name: "الولايات المتحدة",
        flag: "🇺🇸",
        is_active: true,
        created_at: new Date()
    },
    {
        code: "UK",
        name: "المملكة المتحدة",
        flag: "🇬🇧",
        is_active: true,
        created_at: new Date()
    },
    {
        code: "CA",
        name: "كندا",
        flag: "🇨🇦",
        is_active: true,
        created_at: new Date()
    },
    {
        code: "DE",
        name: "ألمانيا",
        flag: "🇩🇪",
        is_active: true,
        created_at: new Date()
    }
]);

db.cards.insertMany([
    {
        card_id: "US_VISA_25",
        card_type: "بطاقة فيزا أمريكية",
        country_code: "US",
        country_name: "الولايات المتحدة",
        value: 25.0,
        price: 25.0,
        currency: "USD",
        is_available: true,
        created_at: new Date()
    },
    {
        card_id: "US_VISA_50",
        card_type: "بطاقة فيزا أمريكية",
        country_code: "US",
        country_name: "الولايات المتحدة",
        value: 50.0,
        price: 50.0,
        currency: "USD",
        is_available: true,
        created_at: new Date()
    },
    {
        card_id: "UK_VISA_25",
        card_type: "بطاقة فيزا بريطانية",
        country_code: "UK",
        country_name: "المملكة المتحدة",
        value: 25.0,
        price: 25.0,
        currency: "GBP",
        is_available: true,
        created_at: new Date()
    },
    {
        card_id: "CA_MASTERCARD_50",
        card_type: "بطاقة ماستركارد كندية",
        country_code: "CA",
        country_name: "كندا",
        value: 50.0,
        price: 50.0,
        currency: "CAD",
        is_available: true,
        created_at: new Date()
    },
    {
        card_id: "DE_VISA_100",
        card_type: "بطاقة فيزا ألمانية",
        country_code: "DE",
        country_name: "ألمانيا",
        value: 100.0,
        price: 100.0,
        currency: "EUR",
        is_available: true,
        created_at: new Date()
    }
]);

print('Database initialized successfully!');
