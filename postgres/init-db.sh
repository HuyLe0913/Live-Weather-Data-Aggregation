#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE iceberg_catalog;
    GRANT ALL PRIVILEGES ON DATABASE iceberg_catalog TO hive;
    -- The 'metastore' db is already created by POSTGRES_DB env var
EOSQL