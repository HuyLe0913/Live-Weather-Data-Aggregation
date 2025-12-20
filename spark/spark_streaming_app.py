"""
Spark Structured Streaming Application

Consumes weather events from Kafka and processes them through two independent paths:
- OLAP path: Aggregates data and writes to Apache Iceberg (historical analytics)
- OLTP path: Writes latest state per city to MongoDB (hot serving layer)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, to_timestamp, window, avg, coalesce, from_unixtime, max as spark_max, 
    min as spark_min, count, current_timestamp, lit, udf
)
from pyspark.sql.types import StringType
import sys
import os
import pandas as pd

# Allow imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from schemas import get_weather_raw_schema
from mongodb.mongodb_writer import MongoDBWriter

# Custom UDFs
def determine_comfort_level(temp, humidity):
    """Derive a human-readable comfort index from temperature and humidity."""
    if temp is None or humidity is None:
        return "Unknown"
    if temp >= 35:
        return "Scorching"
    elif temp >= 30 and humidity > 70:
        return "Muggy"
    elif temp < 15:
        return "Chilly"
    elif 20 <= temp < 30:
        return "Comfortable"
    else:
        return "Moderate"   

# Register the Python function as a Spark UDF  
comfort_udf = udf(determine_comfort_level, StringType())


# ---------------------------------------------------------------------
# Spark Session
# ---------------------------------------------------------------------

def create_spark_session():
    """
    Create and configure a SparkSession with:
        - Kafka source support
        - Hive Metastore connectivity
        - Iceberg catalog integration
        - MinIO (S3A) filesystem support
        - Structured Streaming checkpointing
    """
    return SparkSession.builder \
        .appName(Config.SPARK_APP_NAME) \
        .master(Config.SPARK_MASTER) \
        .config("hive.metastore.uris", Config.HIVE_METASTORE_URI) \
        .config("spark.sql.catalogImplementation", "hive") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.spark_catalog.type", "hive") \
        .config("spark.sql.catalog.spark_catalog.uri", Config.HIVE_METASTORE_URI) \
        .config("spark.sql.catalog.spark_catalog.warehouse", "s3a://weather-data/warehouse") \
        .config("spark.hadoop.fs.s3a.endpoint", Config.MINIO_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", Config.MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", Config.MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.sql.streaming.checkpointLocation", Config.STREAMING_CHECKPOINT_LOCATION) \
        .config("spark.sql.session.timeZone", "Asia/Ho_Chi_Minh") \
        .getOrCreate()


# ---------------------------------------------------------------------
# Kafka Ingestion & Normalization
# ---------------------------------------------------------------------

def process_kafka_stream(spark):
    """
    Read weather events from Kafka and normalize them into a structured DataFrame.
        - Deserialize JSON payload
        - Extract event timestamps with fallbacks
        - Enrich records with derived fields
    """

    # Read from Kafka as a streaming source
    kafka_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", Config.KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", Config.KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Schema for the incoming weather JSON
    weather_schema = get_weather_raw_schema()

    # Parse Kafka key/value and extract timestamps
    weather_df = kafka_df \
        .select(
            col("key").cast(StringType()).alias("message_key"),
            from_json(col("value").cast(StringType()), weather_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ) \
        .select("data.*", "kafka_timestamp") \
        .withColumn(
            "event_timestamp",
            coalesce(
                to_timestamp(col("timestamp")), 
                to_timestamp(from_unixtime(col("dt"))),
                col("kafka_timestamp")
            )
        )
    
    # Add comfort index for downstream use
    weather_df = weather_df.withColumn(
        "comfort_index", 
        comfort_udf(col("temperature"), col("humidity"))
    )
    
    return weather_df


# ---------------------------------------------------------------------
# OLAP Path: Iceberg Analytics
# ---------------------------------------------------------------------

def write_to_iceberg_analytics(weather_df):
    """
    Aggregate weather data into hourly windows and write to Iceberg.
        - Append-only
        - Watermarking for late data
        - Designed for historical analytics and BI queries
    """
    
    # Allow late events up to 10 minutes
    hourly_agg = weather_df \
        .withWatermark("event_timestamp", "10 minutes") \
        .groupBy(
            window(col("event_timestamp"), "1 hour"),
            col("city"),
            col("country")
        ) \
        .agg(
            avg("temperature").alias("avg_temperature"),
            spark_max("temperature").alias("max_temperature"),
            spark_min("temperature").alias("min_temperature"),
            avg("humidity").alias("avg_humidity"),
            avg("pressure").alias("avg_pressure"),
            avg("wind.speed").alias("avg_wind_speed"),
            count("*").alias("record_count")
        )
    
    # Derive comfort index from aggregated values
    hourly_agg = hourly_agg.withColumn(
        "comfort_index",
        comfort_udf(col("avg_temperature"), col("avg_humidity"))
    )
    
    # Write aggregated results to Iceberg
    query = hourly_agg \
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            col("city"),
            col("country"),
            col("avg_temperature"),
            col("max_temperature"),
            col("min_temperature"),
            col("avg_humidity"),
            col("avg_pressure"),
            col("avg_wind_speed"),
            col("comfort_index"),
            col("record_count"),
            current_timestamp().alias("processed_at")
        ) \
        .writeStream \
        .format("iceberg") \
        .outputMode("append") \
        .option("checkpointLocation", f"{Config.STREAMING_CHECKPOINT_LOCATION}/iceberg") \
        .option("path", "spark_catalog.weather_db.hourly_aggregates") \
        .trigger(processingTime="1 minute") \
        .start()
    
    return query


# ---------------------------------------------------------------------
# OLTP Path: MongoDB Serving
# ---------------------------------------------------------------------

def write_to_mongodb_serving(weather_df):
    """
    Write the latest weather state to MongoDB using upsert semantics.
        - One document per city
        - Idempotent writes
        - Optimized for low-latency reads
    """

    def write_batch_to_mongo(batch_df, batch_id):
        """
        Function executed for each micro-batch.
        Converts Spark DataFrame → Pandas → MongoDB upserts.
        """

        try:
            if batch_df.isEmpty(): 
                return

            # Convert to Pandas for easier bulk upsert handling
            pdf = batch_df.toPandas()
            records = pdf.to_dict('records')

            # Normalize NaN values to None for MongoDB
            for record in records:
                for key, value in record.items():
                    if pd.isnull(value):
                        record[key] = None
            
            if records:
                mongo_writer = MongoDBWriter()
                mongo_writer.bulk_upsert_weather(records)
                mongo_writer.close()
                print(f"Batch {batch_id}: Written {len(records)} records to MongoDB.")
                print(f"Sample Comfort Index: {records[0].get('comfort_index', 'N/A')}")

        except Exception as e:
            print(f"Error writing batch {batch_id} to MongoDB: {str(e)}")

    # Attach foreachBatch sink to the streaming query
    query = weather_df \
        .writeStream \
        .foreachBatch(write_batch_to_mongo) \
        .option("checkpointLocation", f"{Config.STREAMING_CHECKPOINT_LOCATION}/mongodb") \
        .trigger(processingTime="30 seconds") \
        .start()
    
    return query


# ---------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------

def main():
    print("Starting Spark Structured Streaming Application...")
    
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"Connected to Spark Master: {Config.SPARK_MASTER}")
    print(f"Reading from Kafka: {Config.KAFKA_BOOTSTRAP_SERVERS}/{Config.KAFKA_TOPIC}")
    
    # Ingest and normalize Kafka stream
    weather_df = process_kafka_stream(spark)
    
    print("Starting dual path processing...")
    
    # OLAP path
    iceberg_query = write_to_iceberg_analytics(weather_df)
    print(" OLAP path started: Writing aggregates to Iceberg")
    
    # OLTP path
    mongodb_query = write_to_mongodb_serving(weather_df)
    print(" OLTP path started: Writing latest data to MongoDB")
    
    print("\n=== Streaming application is running ===")
    print("Press Ctrl+C to stop")
    
    try:
        spark.streams.awaitAnyTermination()
    except KeyboardInterrupt:
        print("\nStopping streams...")
        iceberg_query.stop()
        mongodb_query.stop()
        spark.stop()
        print("Streams stopped successfully")

if __name__ == "__main__":
    main()