# 🚀 Webhook Setup Guide

This guide explains how to set up webhooks for your Telegram bots instead of using polling.

## 🎯 Benefits of Webhooks

- **⚡ Instant delivery**: No 2-3 second delays
- **💰 Zero API calls**: No continuous polling requests
- **🔋 Resource efficient**: Event-driven processing only
- **📈 Better scalability**: Handles high loads efficiently

## 🛠️ Setup Methods

### Method 1: Local Development (ngrok)

For testing webhooks locally:

1. **Install ngrok**:
   ```bash
   # macOS
   brew install ngrok
   
   # Or download from https://ngrok.com/
   ```

2. **Start ngrok tunnel**:
   ```bash
   # For customer bot (port 8443)
   ngrok http 8443
   
   # For order bot (port 8444) - in another terminal
   ngrok http 8444
   ```

3. **Update .env file**:
   ```env
   USE_WEBHOOKS=true
   WEBHOOK_URL=https://abc123.ngrok.io
   WEBHOOK_PORT=8443
   ORDER_WEBHOOK_URL=https://def456.ngrok.io
   ORDER_WEBHOOK_PORT=8444
   ```

4. **Start the bots**:
   ```bash
   make up
   ```

### Method 2: Production Server

For production deployment:

1. **Get SSL certificate** (required for webhooks)
2. **Configure reverse proxy** (nginx/apache)
3. **Update environment variables**:
   ```env
   USE_WEBHOOKS=true
   WEBHOOK_URL=https://yourdomain.com
   WEBHOOK_PORT=8443
   ORDER_WEBHOOK_URL=https://yourdomain.com/order
   ORDER_WEBHOOK_PORT=8444
   ```

## 📊 Configuration Options

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `USE_WEBHOOKS` | Enable/disable webhooks | `false` | `true` |
| `WEBHOOK_URL` | Customer bot webhook URL | - | `https://yourdomain.com` |
| `WEBHOOK_PORT` | Customer bot port | `8443` | `8443` |
| `ORDER_WEBHOOK_URL` | Order bot webhook URL | - | `https://yourdomain.com/order` |
| `ORDER_WEBHOOK_PORT` | Order bot port | `8444` | `8444` |

## 🔄 Switching Between Modes

### Enable Webhooks
```env
USE_WEBHOOKS=true
WEBHOOK_URL=https://yourdomain.com
ORDER_WEBHOOK_URL=https://yourdomain.com/order
```

### Disable Webhooks (fallback to polling)
```env
USE_WEBHOOKS=false
# or simply comment out the webhook URLs
```

## 🧪 Testing Webhooks

1. **Check webhook status**:
   ```bash
   curl -X GET "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
   ```

2. **Monitor logs**:
   ```bash
   docker-compose logs -f telegram-bot
   docker-compose logs -f order-bot
   ```

3. **Expected log output**:
   ```
   INFO:root:Starting bot with webhooks on port 8443...
   INFO:root:Webhook URL: https://yourdomain.com
   ```

## 🚨 Troubleshooting

### Common Issues

1. **SSL Certificate Error**:
   - Webhooks require HTTPS
   - Use ngrok for local testing
   - Get valid SSL certificate for production

2. **Port Not Accessible**:
   - Check firewall settings
   - Ensure ports are exposed in docker-compose.yml
   - Verify reverse proxy configuration

3. **Webhook Not Set**:
   - Check `getWebhookInfo` API response
   - Ensure `WEBHOOK_URL` is accessible from internet
   - Telegram validates webhook URL before setting

### Debug Commands

```bash
# Check if webhook is set
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"

# Delete webhook (fallback to polling)
curl "https://api.telegram.org/bot<BOT_TOKEN>/deleteWebhook"

# Test webhook URL
curl -X POST "https://yourdomain.com/webhook" -H "Content-Type: application/json" -d '{}'
```

## 📈 Performance Comparison

| Metric | Polling | Webhooks |
|--------|---------|----------|
| **Latency** | 2-3 seconds | Instant |
| **API Calls/min** | ~50 | 0 |
| **Resource Usage** | Continuous | Event-driven |
| **Scalability** | Limited | Excellent |
| **Setup Complexity** | Simple | Moderate |

## 🔐 Security Considerations

1. **Use HTTPS only** - Telegram requires SSL
2. **Validate webhook source** - Check Telegram's IP ranges
3. **Use secret tokens** - Add webhook secret validation
4. **Rate limiting** - Implement request rate limits
5. **Input validation** - Validate all incoming data

## 🎉 Next Steps

1. Set up ngrok for local testing
2. Test webhook functionality
3. Deploy to production server with SSL
4. Monitor performance improvements
5. Enjoy instant message delivery! 🚀
