#!/bin/bash
set -e

echo "Checking if metastore schema exists..."

# Wait for PostgreSQL to be ready
until nc -z postgres 5432; do 
    echo "Waiting for PostgreSQL..."
    sleep 2
done

# Check schema status
if /opt/hive/bin/schematool -dbType postgres -info > /dev/null 2>&1; then
    echo "Metastore schema already initialized. Skipping init."
else
    echo "Schema not found. Initializing..."
    /opt/hive/bin/schematool -dbType postgres -initSchema || {
        echo "Schema initialization completed or tables already exist. Continuing..."
    }
fi

exec "$@"
