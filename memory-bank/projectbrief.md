# Project Brief: Telegram Card Sales Bot

## Overview
A Telegram bot system for selling digital cards (gift cards) with USDT payment processing. The bot provides an Arabic interface for users to browse, purchase, and manage digital card transactions.

## Core Requirements

### Primary Functions
1. **User Management**: Registration, profile management, balance tracking
2. **Card Sales**: Browse cards by country, purchase with USDT balance
3. **Payment Processing**: USDT deposit instructions and balance management
4. **Order Management**: Create orders, track purchases, admin notifications
5. **Security**: Blacklist management, user verification

### Technical Requirements
- **Language**: Python with python-telegram-bot library
- **Database**: MongoDB with Motor (async driver)
- **Deployment**: Docker containerization
- **Interface**: Arabic language support
- **Architecture**: Async/await pattern throughout

## Key Business Logic
- Users deposit USDT to purchase cards
- Cards are organized by country and type
- Each card has a price in USDT
- Orders trigger admin notifications for manual fulfillment
- Balance is deducted upon confirmed purchase

## Success Criteria
- Smooth user experience with Arabic interface
- Reliable payment and order processing
- Robust error handling for Telegram API
- Scalable MongoDB data management
- Easy deployment via Docker

## Current Status
- Core functionality implemented
- Recent fix: Telegram API error handling for identical message edits
- Docker deployment ready
- MongoDB integration complete
