#Data schemas, storage metadata and type definitions for weather data pipeline.
from pyspark.sql.types import (StructType, StructField, StringType, DoubleType, IntegerType, TimestampType, MapType, LongType)

def get_weather_raw_schema():
    """
    Schema for raw weather data from API/Kafka.
    Includes 'dt' (Unix timestamp) often used by Weather APIs.
    """
    return StructType([
        StructField("timestamp", StringType(), True), # ISO8601 string
        StructField("dt", LongType(), True),          # Unix timestamp (seconds)
        StructField("city", StringType(), True),
        StructField("country", StringType(), True),
        StructField("coordinates", MapType(StringType(), DoubleType()), True), #latitude/longitude
        StructField("temperature", DoubleType(), True),
        StructField("feels_like", DoubleType(), True), #heat index
        StructField("pressure", IntegerType(), True),
        StructField("humidity", IntegerType(), True),
        StructField("temp_min", DoubleType(), True),
        StructField("temp_max", DoubleType(), True),
        StructField("visibility", IntegerType(), True),
        StructField("wind", MapType(StringType(), DoubleType()), True),
        StructField("clouds", IntegerType(), True),
        StructField("weather", MapType(StringType(), StringType()), True), #description
        StructField("sunrise", IntegerType(), True),
        StructField("sunset", IntegerType(), True),
        StructField("timezone", IntegerType(), True)
    ])

def get_hourly_aggregate_schema():
    """
    Schema for hourly aggregated weather data (Iceberg table).
    """
    return StructType([
        StructField("window_start", TimestampType(), True),
        StructField("window_end", TimestampType(), True),
        StructField("city", StringType(), True),
        StructField("country", StringType(), True),
        StructField("avg_temperature", DoubleType(), True),
        StructField("max_temperature", DoubleType(), True),
        StructField("min_temperature", DoubleType(), True),
        StructField("avg_humidity", DoubleType(), True),
        StructField("avg_pressure", DoubleType(), True),
        StructField("avg_wind_speed", DoubleType(), True),
        StructField("record_count", LongType(), True),
        StructField("processed_at", TimestampType(), True)
    ])

def get_current_weather_schema():
    """
    Schema for current weather data (MongoDB serving path).
    """
    return StructType([
        StructField("timestamp", StringType(), True), # ISO8601 string
        StructField("event_timestamp", TimestampType(), True),
        StructField("city", StringType(), True),
        StructField("country", StringType(), True),
        StructField("coordinates", MapType(StringType(), DoubleType()), True), #latitude/longitude
        StructField("temperature", DoubleType(), True),
        StructField("feels_like", DoubleType(), True), #heat index
        StructField("pressure", IntegerType(), True),
        StructField("humidity", IntegerType(), True),
        StructField("temp_min", DoubleType(), True),
        StructField("temp_max", DoubleType(), True),
        StructField("visibility", IntegerType(), True),
        StructField("wind", MapType(StringType(), DoubleType()), True),
        StructField("clouds", IntegerType(), True),
        StructField("weather", MapType(StringType(), StringType()), True), #description
        StructField("sunrise", IntegerType(), True),
        StructField("sunset", IntegerType(), True),
        StructField("timezone", IntegerType(), True),
        StructField("kafka_timestamp", TimestampType(), True)
    ])

# SQL DDL for Iceberg tables
# Create an hourly aggregated weather table in Iceberg if it does not already exist, matching get_hourly_aggregate_schema().
# Partitions data by day of the aggregation window. Write data in .parquet format - columnar format optimized for analytics.
ICEBERG_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS spark_catalog.weather_db.hourly_aggregates (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    city STRING,
    country STRING,
    avg_temperature DOUBLE,
    max_temperature DOUBLE,
    min_temperature DOUBLE,
    avg_humidity DOUBLE,
    avg_pressure DOUBLE,
    avg_wind_speed DOUBLE,
    record_count BIGINT,
    processed_at TIMESTAMP
) USING iceberg
PARTITIONED BY (days(window_start))
TBLPROPERTIES (
    'write.format.default' = 'parquet',
    'write.parquet.compression-codec' = 'snappy'
)
"""

# MongoDB collection indexes (for optimization)
# Reduce query time complexity from O(n) to O(logn)
MONGO_INDEXES = [
    {"city": 1},  # Index on city for fast lookups, ascending order.
    {"timestamp": -1}  # Index on timestamp for time-based queries, descending order.
]

