# On your build machine (with Docker Buildx)
docker buildx create --use --name multi
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t 135222871115.dkr.ecr.eu-north-1.amazonaws.com/telegram/order-bot:latest \
  --push .
