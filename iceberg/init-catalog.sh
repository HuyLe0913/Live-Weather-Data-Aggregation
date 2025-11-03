#!/bin/sh
echo "Initializing Iceberg Catalog..."

echo "Waiting for services..."
sleep 10

echo "Creating MinIO bucket..."
mc alias set myminio http://minio:9000 rootuser rootpass123
mc mb myminio/weather-data --ignore-existing
mc mb myminio/weather-data/warehouse --ignore-existing

echo "Iceberg catalog initialized!"
echo "Next steps:"
echo "1. Run Spark streaming app to create Iceberg tables"
echo "2. Or use Trino to create tables:"
echo "   docker exec -it trino trino --catalog iceberg --execute 'CREATE SCHEMA IF NOT EXISTS weather_db'"
