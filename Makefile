# Development commands
create_env:
	python -m venv venv && source venv/bin/activate

install_requirements:
	pip install -r requirements.txt

run_bot:
	python bot.py

run_order_bot:
	python order_bot.py

run_support_bot:
	python support_bot.py

run_both_bots:
	python bot.py &
	python order_bot.py

run_all_bots:
	python bot.py &
	python order_bot.py &
	python support_bot.py

# Docker commands
docker-build:
	docker-compose build

up:
	docker-compose up -d --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

docker-clean:
	docker-compose down -v
	docker system prune -f

# MongoDB commands
mongo-shell:
	docker exec -it telegram-bot-mongodb mongosh -u admin -p password123 --authenticationDatabase admin

mongo-backup:
	docker exec telegram-bot-mongodb mongodump --username admin --password password123 --authenticationDatabase admin --db telegram_bot --out /tmp/backup
	docker cp telegram-bot-mongodb:/tmp/backup ./backup

mongo-restore:
	docker cp ./backup telegram-bot-mongodb:/tmp/backup
	docker exec telegram-bot-mongodb mongorestore --username admin --password password123 --authenticationDatabase admin /tmp/backup

mongo-resync:
	docker-compose exec mongodb mongosh --username admin --password password123 --authenticationDatabase admin telegram_bot --file /docker-entrypoint-initdb.d/init-mongo.js

# Development with Docker
dev-up:
	cp env.example .env
	@echo "Please edit .env file with your bot token, then run 'make docker-up'"

dev-setup: dev-up docker-build docker-up

# Cleanup
clean: docker-clean
	rm -rf venv __pycache__ .env


push-bot:
	docker build -t telegram-bot .
	docker tag telegram-bot:latest 135222871115.dkr.ecr.eu-north-1.amazonaws.com/telegram/bot:latest
	docker push 135222871115.dkr.ecr.eu-north-1.amazonaws.com/telegram/bot:latest

push-order-bot:
	docker build -t telegram-order-bot .
	docker tag telegram-order-bot:latest 135222871115.dkr.ecr.eu-north-1.amazonaws.com/telegram/order-bot:latest
	docker push 135222871115.dkr.ecr.eu-north-1.amazonaws.com/telegram/order-bot:latest
