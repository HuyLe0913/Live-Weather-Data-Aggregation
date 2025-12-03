# Apache Iceberg Configuration

Apache Iceberg is an open table format that provides ACID transactions, schema evolution, and time travel queries on your data lake.

## Iceberg in This Project

Iceberg is integrated into the stack through:

1. **Trino** - Query Iceberg tables using SQL
2. **Spark** - Process and write to Iceberg tables
3. **Hive Metastore** - Stores table metadata
4. **MinIO** - Stores actual table data (Parquet files)
5. **Iceberg REST Catalog** - REST API for catalog operations

## Services

### Iceberg REST Catalog Server
- **Port**: 8181
- **API Endpoint**: http://localhost:8181
- **Purpose**: REST API for managing Iceberg catalogs and tables

### Trino Iceberg Connector
- **Catalog**: `iceberg` (configured in `trino/catalog.properties`)
- **Warehouse**: `s3a://weather-data/warehouse`
- **Metadata**: Stored in Hive Metastore

### Spark Iceberg Support
- Configured in `spark_streaming_app.py`
- Uses `org.apache.iceberg.spark.SparkCatalog`
- Connects to Hive Metastore for metadata

## Table Storage

Iceberg tables are stored in:
- **Metadata**: Hive Metastore (PostgreSQL)
- **Data**: MinIO/S3 (`s3a://weather-data/warehouse`)
- **Format**: Parquet files
- **Compression**: Snappy

## Usage Examples

### Query with Trino

```sql
-- Connect to Trino and use Iceberg catalog
USE iceberg.weather_db;

-- Query Iceberg table
SELECT * FROM hourly_aggregates LIMIT 10;

-- Time travel query (if supported)
SELECT * FROM hourly_aggregates FOR VERSION AS OF '2025-11-03';
```

### Create Table via Spark

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkCatalog") \
    .getOrCreate()

spark.sql("""
    CREATE TABLE IF NOT EXISTS spark_catalog.weather_db.hourly_aggregates (
        window_start TIMESTAMP,
        city STRING,
        avg_temperature DOUBLE,
        ...
    ) USING iceberg
    PARTITIONED BY (days(window_start))
""")
```

### REST API Operations

```bash
# List catalogs
curl http://localhost:8181/v1/config

# List tables in a namespace
curl http://localhost:8181/v1/namespaces/weather_db/tables

# Get table metadata
curl http://localhost:8181/v1/namespaces/weather_db/tables/hourly_aggregates
```

## Configuration Files

- **Trino**: `trino/catalog.properties`
- **Spark**: `spark_streaming_app.py` (create_spark_session function)
- **Hive Metastore**: `hive/metastore-site.xml`

## Features

✅ **ACID Transactions** - Safe concurrent writes
✅ **Schema Evolution** - Add/remove columns safely
✅ **Time Travel** - Query historical data versions
✅ **Hidden Partitioning** - Automatic partition management
✅ **Metadata Management** - Efficient metadata operations
✅ **Parquet Format** - Columnar storage for analytics

## Troubleshooting

### Tables not showing in Trino
- Ensure Hive Metastore is running
- Check Trino catalog configuration
- Verify MinIO connection

### Spark can't write to Iceberg
- Check Hive Metastore connection
- Verify S3/MinIO credentials
- Check Spark Iceberg extensions are loaded

### REST API not accessible
- Check Iceberg REST service is running
- Verify port 8181 is not blocked
- Check service logs: `docker-compose logs iceberg-rest`

## Resources

- [Iceberg Documentation](https://iceberg.apache.org/)
- [Trino Iceberg Connector](https://trino.io/docs/current/connector/iceberg.html)
- [Spark Iceberg Integration](https://iceberg.apache.org/spark/)

