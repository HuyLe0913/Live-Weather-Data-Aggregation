# Trino Configuration

This directory contains Trino configuration files for connecting to **Apache Iceberg** tables on MinIO.

## Configuration

The `catalog.properties` file configures the **Iceberg connector** to:
- Connect to MinIO (S3-compatible storage) for table data
- Connect to Hive Metastore for table metadata
- Query Iceberg tables stored in Parquet format

## Iceberg Support

Trino uses the Iceberg connector to query tables with:
- ACID transactions
- Schema evolution
- Time travel queries
- Hidden partitioning

## Access Trino

After starting with docker-compose:
- **Web UI**: http://localhost:8090
- **REST API**: http://localhost:8090/v1/

## Query Examples

Connect to Trino:
```bash
# Using Trino CLI (if installed)
trino --server http://localhost:8090

# Or via REST API
curl http://localhost:8090/v1/statement --data "SELECT * FROM hive.weather_db.hourly_aggregates LIMIT 10"
```

## Superset Connection

When connecting Superset to Trino:
- **SQLAlchemy URI**: `trino://trino@trino:8080/hive/weather_db`
- Use service name `trino` (not localhost) when connecting from Superset container

