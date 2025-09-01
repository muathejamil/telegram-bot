# Two Bots Setup Guide

## Overview

This project now supports **two separate Telegram bots**:

1. **Main Bot** (`bot.py`) - Customer-facing bot for card purchases
2. **Order Management Bot** (`order_bot.py`) - Admin-only bot for managing orders

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Customer Bot  │    │  Order Mgmt Bot │
│    (bot.py)     │    │ (order_bot.py)  │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
            ┌────────▼────────┐
            │    MongoDB      │
            │   (Shared DB)   │
            └─────────────────┘
```

## Configuration

### Environment Variables Required

```bash
# Customer Bot Token
BOT_TOKEN=your_customer_bot_token_here

# Order Management Bot Token  
ORDER_BOT_TOKEN=your_order_management_bot_token_here

# Admin User ID (for order bot access)
ADMIN_USER_ID=your_telegram_user_id

# Payment Configuration
BINANCE_WALLET_TOKEN=your_wallet_address
BINANCE_WALLET_ID=your_binance_id
```

### Creating Two Bots with BotFather

1. **Create Customer Bot:**
   ```
   /newbot
   Name: Your Store Bot
   Username: your_store_bot
   ```

2. **Create Order Management Bot:**
   ```
   /newbot  
   Name: Your Store Admin Bot
   Username: your_store_admin_bot
   ```

3. **Get both tokens and add to `.env` file**

## Deployment Options

### Option 1: Docker (Recommended)

Both bots run in separate containers:

```bash
# Build and start both bots
make up

# Check logs
docker-compose logs telegram-bot    # Customer bot
docker-compose logs order-bot       # Order management bot

# Stop both bots
make docker-down
```

### Option 2: Local Development

Run both bots locally:

```bash
# Terminal 1 - Customer Bot
make run_bot

# Terminal 2 - Order Management Bot  
make run_order_bot

# Or run both in background
make run_both_bots
```

## Bot Features

### Customer Bot (`bot.py`)
- ✅ User registration and profiles
- ✅ Card browsing by country
- ✅ USDT balance management
- ✅ Purchase flow with confirmation
- ✅ Order creation and notifications
- ✅ Arabic interface with error handling

### Order Management Bot (`order_bot.py`)
- ✅ Admin-only access control
- ✅ Pending orders management
- ✅ Order completion tracking
- ✅ Card inventory management (planned)
- ✅ User management (planned)
- ✅ Sales statistics (planned)

## Database Schema

Both bots share the same MongoDB database with these collections:

- **users** - Customer profiles and balances
- **cards** - Available cards inventory
- **orders** - Purchase orders (shared between bots)
- **transactions** - Payment history
- **blacklist** - Blocked users
- **countries** - Available countries

## Security

### Access Control
- **Customer Bot**: Open to all users (with blacklist checking)
- **Order Bot**: Restricted to admin user ID only

### Data Isolation
- Both bots share the same database
- Order bot has additional methods for admin operations
- Customer bot cannot access admin functions

## Monitoring

### Health Checks
```bash
# Check if both containers are running
docker-compose ps

# View real-time logs
docker-compose logs -f telegram-bot
docker-compose logs -f order-bot
```

### Log Locations
- Customer Bot: `telegram-bot-app` container
- Order Bot: `telegram-order-bot-app` container
- Database: `telegram-bot-mongodb` container

## Troubleshooting

### Common Issues

1. **Order bot not responding**
   - Check `ORDER_BOT_TOKEN` is set correctly
   - Verify `ADMIN_USER_ID` matches your Telegram ID

2. **Database connection errors**
   - Ensure MongoDB container is running
   - Check network connectivity between containers

3. **Permission denied on order bot**
   - Verify you're using the correct admin user ID
   - Check environment variable is loaded correctly

### Getting Your Telegram User ID

Send `/start` to any bot and check the logs, or use:
```bash
# Check customer bot logs for your user ID
docker-compose logs telegram-bot | grep "ID:"
```

## Benefits of Two-Bot Architecture

### ✅ **Separation of Concerns**
- Customer operations isolated from admin functions
- Cleaner code organization
- Independent scaling

### ✅ **Security**
- Admin functions not exposed to customers
- Different access controls per bot
- Reduced attack surface

### ✅ **Maintenance**
- Can update/restart bots independently
- Easier debugging and monitoring
- Clear responsibility boundaries

### ✅ **Scalability**
- Customer bot can handle high user load
- Admin bot optimized for management tasks
- Independent resource allocation

## Next Steps

1. **Test both bots** with your tokens
2. **Configure admin user ID** for order bot access
3. **Implement additional admin features** as needed
4. **Set up monitoring** for production use

The two-bot architecture provides a robust, scalable solution for your card sales platform!
