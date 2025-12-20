#!/bin/bash
# Exit immediately if any command fails.
# Prevents partial or inconsistent database initialization.

# Create a dedicated database for the Iceberg catalog
# This database is used by Hive Metastore to store Iceberg-related metadata

# Grant full privileges on the Iceberg catalog database to the Hive user
# Hive Metastore connects using this user to read/write metadata

set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE iceberg_catalog;
    GRANT ALL PRIVILEGES ON DATABASE iceberg_catalog TO hive;
    -- The 'metastore' db is already created by POSTGRES_DB env var
EOSQL