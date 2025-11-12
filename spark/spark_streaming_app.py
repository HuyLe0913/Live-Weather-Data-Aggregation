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

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from schemas import get_weather_raw_schema
from mongodb_writer import MongoDBWriter

def create_spark_session():
    """Create Spark session with Iceberg and Kafka support."""
    return SparkSession.builder \
        .appName(Config.SPARK_APP_NAME) \
        .master(Config.SPARK_MASTER) \
        .config("spark.jars", 
                "/opt/spark/jars/spark-sql-kafka-0-10_2.12-3.5.1.jar,"
                "/opt/spark/jars/iceberg-spark-runtime-3.5_2.12-1.4.3.jar,"
                "/opt/spark/jars/hadoop-aws-3.3.4.jar,"
                "/opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar") \
        .config("spark.sql.extensions", 
                "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.spark_catalog", 
                "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.spark_catalog.type", "hive") \
        .config("spark.sql.catalog.spark_catalog.uri", 
                Config.HIVE_METASTORE_URI) \
        .config("spark.hadoop.fs.s3a.endpoint", Config.MINIO_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", Config.MINIO_ACCESS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", Config.MINIO_SECRET_KEY) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", 
                "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.sql.streaming.checkpointLocation", 
                Config.STREAMING_CHECKPOINT_LOCATION) \
        .getOrCreate()

def process_kafka_stream(spark):
    """Read and process Kafka stream."""
    
    # Read from Kafka
    kafka_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", Config.KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", Config.KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Parse JSON
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
    """
    Path 1: OLAP - Write aggregated data to Iceberg for analytics.
    Aggregates data into hourly windows.
    """
    
    # Hourly aggregation with watermark for late data
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
    
    # Write to Iceberg table
    query = hourly_agg \
        .writeStream \
        .format("iceberg") \
        .outputMode("append") \
        .option("checkpointLocation", 
                f"{Config.STREAMING_CHECKPOINT_LOCATION}/iceberg") \
        .option("path", 
                "spark_catalog.weather_db.hourly_aggregates") \
        .trigger(processingTime="5 minutes") \
        .start()
    
    return query

def write_to_mongodb_serving(weather_df):
    """
    Path 2: OLTP - Write latest weather to MongoDB for serving applications.
    """
    
    def write_batch_to_mongo(batch_df, batch_id):
        """Write batch to MongoDB."""
        try:
            # Convert to pandas for easier MongoDB writing
            records = batch_df.toPandas().to_dict('records')
            
            if records:
                mongo_writer = MongoDBWriter()
                mongo_writer.bulk_upsert_weather(records)
                mongo_writer.close()
                
                print(f"Batch {batch_id}: Written {len(records)} records to MongoDB")
        except Exception as e:
            print(f"Error writing batch {batch_id} to MongoDB: {str(e)}")
    
    # Write to MongoDB using foreachBatch
    query = weather_df \
        .writeStream \
        .foreachBatch(write_batch_to_mongo) \
        .option("checkpointLocation", 
                f"{Config.STREAMING_CHECKPOINT_LOCATION}/mongodb") \
        .trigger(processingTime="30 seconds") \
        .start()
    
    return query

def main():
    """Main streaming application."""
    print("Starting Spark Structured Streaming Application...")
    
    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"Connected to Spark Master: {Config.SPARK_MASTER}")
    print(f"Reading from Kafka: {Config.KAFKA_BOOTSTRAP_SERVERS}/{Config.KAFKA_TOPIC}")
    
    # Process Kafka stream
    weather_df = process_kafka_stream(spark)
    
    # Dual path processing
    print("Starting dual path processing...")
    
    # Path 1: Analytics (Iceberg)
    iceberg_query = write_to_iceberg_analytics(weather_df)
    print(" OLAP path started: Writing aggregates to Iceberg")
    
    # Path 2: Serving (MongoDB)
    mongodb_query = write_to_mongodb_serving(weather_df)
    print(" OLTP path started: Writing latest data to MongoDB")
    
    # Wait for termination
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