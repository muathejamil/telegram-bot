// MongoDB initialization script
db = db.getSiblingDB('telegram_bot');

// Create collections
db.createCollection('users');
db.createCollection('cards');
db.createCollection('transactions');
db.createCollection('blacklist');
db.createCollection('countries');
db.createCollection('orders');
db.createCollection('notifications');
db.createCollection('black_websites');
db.createCollection('support_conversations');
db.createCollection('support_stats');

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
db.notifications.createIndex({ "notification_id": 1 }, { unique: true });
db.notifications.createIndex({ "status": 1 });
db.notifications.createIndex({ "type": 1 });
db.notifications.createIndex({ "created_at": 1 });
db.black_websites.createIndex({ "website_id": 1 }, { unique: true });
db.black_websites.createIndex({ "is_available": 1 });
db.black_websites.createIndex({ "is_deleted": 1 });
db.black_websites.createIndex({ "name": 1 });
db.support_conversations.createIndex({ "user_id": 1 });
db.support_conversations.createIndex({ "status": 1 });
db.support_conversations.createIndex({ "created_at": 1 });
db.support_conversations.createIndex({ "last_message_at": 1 });
db.support_conversations.createIndex([{ "status": 1 }, { "last_message_at": -1 }]);
db.support_conversations.createIndex([{ "user_id": 1 }, { "status": 1 }], { unique: true, partialFilterExpression: { "status": "active" } });
db.support_stats.createIndex({ "date": 1 }, { unique: true });

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

// Insert sample black websites
db.black_websites.insertMany([
    {
        website_id: "bw_1",
        name: "موقع التسوق الأسود",
        url: "https://example-black-site1.com",
        price: 15.0,
        description: "موقع متخصص في بيع المنتجات الرقمية والخدمات الحصرية. يحتوي على مجموعة واسعة من الأدوات والبرامج المفيدة.",
        is_available: true,
        is_deleted: false,
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        website_id: "bw_2",
        name: "موقع الخدمات المحظورة",
        url: "https://example-black-site2.com",
        price: 25.0,
        description: "منصة تقدم خدمات حصرية ومتقدمة. يتطلب تسجيل دخول خاص ويحتوي على محتوى عالي الجودة.",
        is_available: true,
        is_deleted: false,
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        website_id: "bw_3",
        name: "منصة التجارة السوداء",
        url: "https://example-black-site3.com",
        price: 35.0,
        description: "موقع تجاري متقدم يوفر وصولاً إلى أسواق خاصة ومنتجات حصرية. يشمل دعم فني على مدار الساعة.",
        is_available: true,
        is_deleted: false,
        created_at: new Date(),
        updated_at: new Date()
    }
]);

// Insert sample notifications for testing
db.notifications.insertMany([
    {
        notification_id: "notif_sample_1",
        type: "new_order",
        data: {
            order_id: "order_sample_1",
            user: {
                id: 123456789,
                first_name: "أحمد",
                username: "ahmed_test"
            },
            card: {
                card_type: "بطاقة فيزا أمريكية",
                country_name: "الولايات المتحدة",
                price: 25.0
            },
            timestamp: "2025-09-01 21:30:00"
        },
        status: "pending",
        created_at: new Date(),
        processed_at: null
    },
    {
        notification_id: "notif_sample_2",
        type: "new_order",
        data: {
            order_id: "order_sample_2",
            user: {
                id: 987654321,
                first_name: "فاطمة",
                username: "fatima_test"
            },
            card: {
                card_type: "بطاقة ماستركارد بريطانية",
                country_name: "المملكة المتحدة",
                price: 50.0
            },
            timestamp: "2025-09-01 21:35:00"
        },
        status: "processed",
        created_at: new Date(Date.now() - 300000), // 5 minutes ago
        processed_at: new Date()
    }
]);

print('Database initialized successfully with notifications and black websites collections!');
