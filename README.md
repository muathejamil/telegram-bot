# Telegram Bot with MongoDB Integration

A Telegram bot for managing card sales with MongoDB database integration using Docker.

## Features

- 🤖 Interactive Telegram bot with Arabic interface
- 🗄️ MongoDB database for data persistence
- 🐳 Docker containerization for easy deployment
- 💳 Card management system
- 👥 User profile management
- 💰 Balance tracking
- 🚫 Blacklist functionality
- 📊 Transaction history

## Prerequisites

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd telegram-bot
   ```

2. **Set up environment**
   ```bash
   make dev-up
   ```
   This will create a `.env` file from the example template.

3. **Configure your bot token**
   Edit the `.env` file and add your bot token:
   ```bash
   BOT_TOKEN=your_bot_token_here
   ```

4. **Build and run with Docker**
   ```bash
   make docker-build
   make docker-up
   ```

5. **Check logs**
   ```bash
   make docker-logs
   ```

## Available Commands

### Docker Commands
- `make docker-build` - Build Docker containers
- `make docker-up` - Start services in background
- `make docker-down` - Stop services
- `make docker-logs` - View logs
- `make docker-restart` - Restart services
- `make docker-clean` - Stop services and clean up

### MongoDB Commands
- `make mongo-shell` - Access MongoDB shell
- `make mongo-backup` - Backup database
- `make mongo-restore` - Restore database

### Development Commands
- `make create_env` - Create Python virtual environment
- `make install_requirements` - Install Python dependencies
- `make run_bot` - Run bot locally (requires local setup)

## Project Structure

```
telegram-bot/
├── bot.py                 # Main bot application
├── database.py           # MongoDB operations and models
├── docker-compose.yml    # Docker services configuration
├── Dockerfile           # Bot container configuration
├── init-mongo.js        # MongoDB initialization script
├── requirements.txt     # Python dependencies
├── env.example         # Environment variables template
├── Makefile           # Build and deployment commands
└── README.md          # This file
```

## Database Schema

### Collections

1. **users** - User profiles and balances
2. **cards** - Available cards for purchase
3. **transactions** - Transaction history
4. **blacklist** - Blacklisted users

### Sample Data

The database is initialized with sample data including:
- Sample user account
- Demo cards (VISA and MASTERCARD)
- Proper indexes for performance

## Bot Features

### Main Menu Options

- 👨‍💼 **Profile** - View user profile and balance
- 💸 **Deposit USDT** - Instructions for depositing funds
- 🚒 **Card List** - Browse available cards
- 🤔 **How to Use** - Bot usage instructions
- 💳 **Card Replacement** - Replacement terms and conditions
- ❌ **Blacklist** - Blacklist information

### Security Features

- Automatic blacklist checking
- User registration on first interaction
- Transaction logging
- Balance management

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | Required |
| `MONGODB_URL` | MongoDB connection string | `mongodb://admin:password123@mongodb:27017/telegram_bot?authSource=admin` |
| `DEBUG` | Enable debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |

## MongoDB Access

### Default Credentials
- **Username:** admin
- **Password:** password123
- **Database:** telegram_bot
- **Port:** 27017

### Accessing MongoDB Shell
```bash
make mongo-shell
```

### Database Operations
```javascript
// Switch to telegram_bot database
use telegram_bot

// View collections
show collections

// Query users
db.users.find()

// Query available cards
db.cards.find({is_available: true})
```

## Development

### Local Development Setup

1. Create virtual environment:
   ```bash
   make create_env
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   make install_requirements
   ```

3. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. Start MongoDB with Docker:
   ```bash
   docker-compose up -d mongodb
   ```

5. Run bot locally:
   ```bash
   make run_bot
   ```

### Adding New Features

1. **Database Operations**: Add new methods to `database.py`
2. **Bot Handlers**: Add new handlers to `bot.py`
3. **Database Schema**: Update `init-mongo.js` for new collections

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if bot token is correct
   - Verify bot is running: `make docker-logs`

2. **Database connection failed**
   - Ensure MongoDB container is running
   - Check MongoDB logs: `docker logs telegram-bot-mongodb`

3. **Permission denied errors**
   - Ensure Docker has proper permissions
   - Try running with sudo if necessary

### Logs and Debugging

```bash
# View all logs
make docker-logs

# View specific service logs
docker-compose logs telegram-bot
docker-compose logs mongodb

# Check container status
docker-compose ps
```

## Security Considerations

- Change default MongoDB credentials in production
- Use environment variables for sensitive data
- Enable MongoDB authentication
- Consider using Docker secrets for production deployment
- Regularly backup your database

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team.
