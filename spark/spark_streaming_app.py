"""
Spark Structured Streaming Application
Consumes weather data from Kafka and writes to Iceberg (OLAP) and MongoDB (OLTP)
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, to_timestamp, window, avg, max as spark_max, 
    min as spark_min, count, current_timestamp, lit
)
from pyspark.sql.types import StringType
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from schemas import get_weather_raw_schema
from mongodb_writer import MongoDBWriter

def create_spark_session():
    """Create Spark session with Iceberg, Kafka, and Checkpointing support."""
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
        .getOrCreate()

def init_iceberg_resources(spark):
    """Initialize Iceberg Database and Table with correct S3 location."""
    print("Initializing Iceberg Database and Table...")
    
    try:
        # 1. Clean up potential bad state (Optional, but good for dev)
        spark.sql("DROP DATABASE IF EXISTS spark_catalog.weather_db CASCADE")
        
        # 2. Create Database with explicit S3 Location
        spark.sql(f"""
            CREATE DATABASE IF NOT EXISTS spark_catalog.weather_db
            LOCATION 's3a://weather-data/warehouse/weather_db'
        """)
        
        # 3. Create Table
        spark.sql("""
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
                record_count LONG,
                processed_at TIMESTAMP
            ) USING iceberg
            PARTITIONED BY (city)
        """)
        print("✓ Iceberg table initialized successfully in S3!")
        
    except Exception as e:
        print(f"⚠ Warning during initialization: {e}")
        # We don't exit here; we let the stream try to run even if init had issues.

def process_kafka_stream(spark):
    kafka_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", Config.KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", Config.KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    weather_schema = get_weather_raw_schema()
    
    weather_df = kafka_df \
        .select(
            col("key").cast(StringType()).alias("message_key"),
            from_json(col("value").cast(StringType()), weather_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ) \
        .select("data.*", "kafka_timestamp") \
        .withColumn("event_timestamp", to_timestamp(col("timestamp")))
    
    return weather_df

def write_to_iceberg_analytics(weather_df):
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
        ) \
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
            col("record_count"),
            current_timestamp().alias("processed_at")
        )
    
    query = hourly_agg \
        .writeStream \
        .format("iceberg") \
        .outputMode("append") \
        .option("checkpointLocation", f"{Config.STREAMING_CHECKPOINT_LOCATION}/iceberg") \
        .option("path", "spark_catalog.weather_db.hourly_aggregates") \
        .trigger(processingTime="1 minute") \
        .start()
    
    return query

def write_to_mongodb_serving(weather_df):
    def write_batch_to_mongo(batch_df, batch_id):
        try:
            if batch_df.isEmpty(): return
            records = batch_df.toPandas().to_dict('records')
            if records:
                mongo_writer = MongoDBWriter()
                mongo_writer.bulk_upsert_weather(records)
                mongo_writer.close()
                print(f"Batch {batch_id}: Written {len(records)} records to MongoDB")
        except Exception as e:
            print(f"Error writing batch {batch_id} to MongoDB: {str(e)}")
    
    query = weather_df \
        .writeStream \
        .foreachBatch(write_batch_to_mongo) \
        .option("checkpointLocation", f"{Config.STREAMING_CHECKPOINT_LOCATION}/mongodb") \
        .trigger(processingTime="30 seconds") \
        .start()
    
    return query

def main():
    print("Starting Spark Structured Streaming Application...")
    
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"Connected to Spark Master: {Config.SPARK_MASTER}")
    
    # Initialize Metadata (Create DB/Table) without waiting loop
    init_iceberg_resources(spark)

    print(f"Reading from Kafka: {Config.KAFKA_BOOTSTRAP_SERVERS}/{Config.KAFKA_TOPIC}")
    
    weather_df = process_kafka_stream(spark)
    
    print("Starting dual path processing...")
    iceberg_query = write_to_iceberg_analytics(weather_df)
    print(" OLAP path started: Writing aggregates to Iceberg")
    
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