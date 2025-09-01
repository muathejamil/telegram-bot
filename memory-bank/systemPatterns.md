# System Patterns: Telegram Card Sales Bot

## Architecture Overview

### High-Level Architecture
```
User (Telegram) → Bot Handler → Database Manager → MongoDB
                      ↓
                Admin Notifications
```

### Core Components
1. **bot.py**: Main application with Telegram handlers
2. **database.py**: MongoDB operations and data models
3. **Docker Environment**: Containerized deployment
4. **MongoDB**: Data persistence layer

## Key Technical Decisions

### Async/Await Pattern
- **Why**: Telegram bot requires non-blocking operations
- **Implementation**: All database operations and bot handlers use async/await
- **Benefit**: Can handle multiple users simultaneously

### MongoDB with Motor
- **Why**: Async MongoDB driver compatible with bot architecture
- **Collections**: users, cards, transactions, blacklist, countries, orders
- **Indexing**: Optimized queries for user lookups and card searches

### Error Handling Strategy
- **Telegram API Errors**: Custom `safe_edit_message()` function
- **Database Errors**: Try-catch with logging and user feedback
- **Graceful Degradation**: Fallback responses when operations fail

## Design Patterns in Use

### Handler Pattern
```python
# Command handlers for different bot interactions
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
```

### Repository Pattern
```python
# DatabaseManager encapsulates all data operations
class DatabaseManager:
    async def get_user(self, user_id: int)
    async def create_order(self, user_id: int, card_id: str, ...)
```

### State Management
- **Stateless Design**: Each interaction is independent
- **Context Passing**: User state maintained through callback data
- **Session Persistence**: MongoDB stores all persistent data

## Component Relationships

### Bot → Database Flow
1. User interaction triggers handler
2. Handler validates user (blacklist check)
3. Database operations performed
4. Response sent to user
5. Admin notifications if needed

### Data Flow
```
User Input → Validation → Business Logic → Database Update → Response
```

### Error Propagation
```
Database Error → Log Error → User-Friendly Message → Fallback Action
```

## Security Patterns

### Input Validation
- User ID validation for all operations
- Balance checks before purchases
- Card availability verification

### Access Control
- Blacklist checking on every interaction
- Admin-only operations (notifications)
- User isolation (can only access own data)

### Data Integrity
- Transaction logging for all balance changes
- Order tracking with unique IDs
- Audit trail for all user actions

## Performance Patterns

### Database Optimization
- Indexed collections for fast lookups
- Async operations prevent blocking
- Connection pooling via Motor

### Memory Management
- Stateless handlers reduce memory usage
- Minimal data caching
- Efficient query patterns

### Scalability Considerations
- Horizontal scaling ready (stateless design)
- Database connection management
- Docker containerization for easy deployment
