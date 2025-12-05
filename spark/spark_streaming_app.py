"""
Spark Structured Streaming Application
Consumes weather data from Kafka and writes to Iceberg (OLAP) and MongoDB (OLTP)
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, to_timestamp, window, avg, coalesce, from_unixtime, max as spark_max, 
    min as spark_min, count, current_timestamp, lit
)
from pyspark.sql.types import StringType
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from schemas import get_weather_raw_schema
from mongodb.mongodb_writer import MongoDBWriter

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

def process_kafka_stream(spark):
    """Read and process Kafka stream."""
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
        .withColumn(
            "event_timestamp",
            # 1. Nếu có 'timestamp' (string), thử ép kiểu.
            # 2. Nếu không, dùng 'dt' (long) convert sang timestamp.
            # 3. Nếu cả 2 null, dùng giờ Kafka nhận được (kafka_timestamp).
            coalesce(
                to_timestamp(col("timestamp")), 
                to_timestamp(from_unixtime(col("dt"))),
                col("kafka_timestamp")
            )
        )
    
    return weather_df

def write_to_iceberg_analytics(weather_df):
    """Path 1: OLAP - Write aggregated data to Iceberg."""
    hourly_agg = weather_df \
        .withWatermark("event_timestamp", "1 minutes") \
        .groupBy(
            window(col("event_timestamp"), "5 minutes"),
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
    """Path 2: OLTP - Write latest weather to MongoDB."""
    def write_batch_to_mongo(batch_df, batch_id):
        try:
            if batch_df.isEmpty(): return
            
            # Convert to Pandas
            pdf = batch_df.toPandas()
            records = pdf.to_dict('records')
            for record in records:
                for key, value in record.items():
                    if pd.isnull(value):
                        record[key] = None

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
    print(f"Reading from Kafka: {Config.KAFKA_BOOTSTRAP_SERVERS}/{Config.KAFKA_TOPIC}")
    
    # Process Kafka stream
    weather_df = process_kafka_stream(spark)
    
    print("Starting dual path processing...")
    
    # Path 1: Analytics (Iceberg)
    iceberg_query = write_to_iceberg_analytics(weather_df)
    print(" OLAP path started: Writing aggregates to Iceberg")
    
    # Path 2: Serving (MongoDB)
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