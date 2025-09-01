# Technical Context: Telegram Card Sales Bot

## Technology Stack

### Core Technologies
- **Python 3.12**: Main programming language
- **python-telegram-bot 22.3**: Telegram Bot API wrapper
- **MongoDB**: NoSQL database for data persistence
- **Motor 3.6.0**: Async MongoDB driver
- **Docker**: Containerization and deployment

### Key Dependencies
```
python-telegram-bot==22.3  # Telegram Bot API
motor==3.6.0               # Async MongoDB driver
pymongo==4.9.0             # MongoDB operations
python-dotenv==1.0.1       # Environment variable management
APScheduler==3.10.4        # Task scheduling (if needed)
```

## Development Setup

### Environment Requirements
- **Python**: 3.12+
- **Docker**: Latest version with Docker Compose
- **MongoDB**: 7.0+ (via Docker)

### Local Development
```bash
# Virtual environment setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Environment configuration
cp env.example .env
# Edit .env with your bot token and settings
```

### Docker Development
```bash
# Build and start services
make docker-build
make docker-up

# View logs
make docker-logs

# Access MongoDB shell
make mongo-shell
```

## Technical Constraints

### Telegram API Limitations
- **Rate Limits**: 30 messages per second per bot
- **Message Size**: 4096 characters max
- **File Size**: 50MB max for files
- **Edit Restrictions**: Cannot edit with identical content

### MongoDB Considerations
- **Connection Limits**: Default 100 concurrent connections
- **Document Size**: 16MB max per document
- **Index Limitations**: 64 indexes max per collection

### Docker Environment
- **Memory**: Minimum 512MB recommended
- **Storage**: Persistent volumes for MongoDB data
- **Network**: Internal Docker network for service communication

## Configuration Management

### Environment Variables
```bash
# Required
BOT_TOKEN=your_telegram_bot_token
ADMIN_USER_ID=your_telegram_user_id

# Optional (with defaults)
MONGODB_URL=mongodb://admin:password123@mongodb:27017/telegram_bot?authSource=admin
DEBUG=False
LOG_LEVEL=INFO

# Payment Configuration
BINANCE_WALLET_TOKEN=your_binance_wallet_address
BINANCE_WALLET_ID=your_binance_id
```

### Database Configuration
- **Default Credentials**: admin/password123
- **Database Name**: telegram_bot
- **Collections**: users, cards, transactions, blacklist, countries, orders
- **Indexes**: Automatically created via init-mongo.js

## Deployment Architecture

### Production Setup
```yaml
# docker-compose.yml structure
services:
  telegram-bot:
    build: .
    depends_on: [mongodb]
    environment: [env variables]
  
  mongodb:
    image: mongo:7.0
    volumes: [persistent storage]
    environment: [auth settings]
```

### Scaling Considerations
- **Horizontal Scaling**: Multiple bot instances possible
- **Database Scaling**: MongoDB replica sets for high availability
- **Load Balancing**: Not required (Telegram handles routing)

## Security Configuration

### Bot Security
- **Token Management**: Environment variables only
- **User Validation**: Blacklist checking on every interaction
- **Input Sanitization**: Automatic via Telegram API

### Database Security
- **Authentication**: Username/password required
- **Network**: Internal Docker network only
- **Backup**: Regular automated backups recommended

### Operational Security
- **Logging**: Structured logging with levels
- **Monitoring**: Docker health checks
- **Error Handling**: No sensitive data in error messages

## Development Workflow

### Code Organization
```
telegram-bot/
├── bot.py              # Main bot logic
├── database.py         # Data layer
├── requirements.txt    # Dependencies
├── Dockerfile         # Container config
├── docker-compose.yml # Service orchestration
├── init-mongo.js      # DB initialization
├── Makefile          # Build commands
└── memory-bank/      # Project documentation
```

### Testing Strategy
- **Manual Testing**: Via Telegram interface
- **Database Testing**: Direct MongoDB queries
- **Integration Testing**: Docker environment testing
- **Error Testing**: Simulate API failures

### Deployment Process
1. Update code and commit changes
2. Build Docker images: `make docker-build`
3. Start services: `make docker-up`
4. Verify functionality: `make docker-logs`
5. Monitor for errors and performance
