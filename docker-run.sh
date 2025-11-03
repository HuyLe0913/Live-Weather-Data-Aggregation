#!/bin/bash
# Quick script to run the weather data collector with Docker

set -e

echo "=== Weather Data Collector - Docker Setup ==="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with:"
    echo "  OPENWEATHER_API_KEY=your_api_key_here"
    echo "  CITIES=Hanoi,Ho Chi Minh City,Da Nang"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed!"
    exit 1
fi

echo "📦 Starting infrastructure services (Kafka, MongoDB, MinIO)..."
docker-compose up -d zookeeper kafka mongodb minio

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🔨 Building data collector image..."
docker-compose build data-collector

echo "🚀 Starting data collector..."
docker-compose up -d data-collector

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f data-collector"
echo ""
echo "🔍 Check Kafka messages:"
echo "   docker exec -it kafka kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic weather-data --from-beginning"
echo ""
echo "💾 Check MongoDB data:"
echo "   docker exec -it mongodb mongosh weather_db --eval 'db.current_weather.find().pretty()'"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""

