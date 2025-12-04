from pyspark.sql import SparkSession
import sys
import time

def init_warehouse():
    print("--- Initializing Iceberg Warehouse ---")
    
    # Initialize Spark with Hive support
    spark = SparkSession.builder \
        .appName("IcebergInit") \
        .config("hive.metastore.uris", "thrift://hive-metastore:9083") \
        .config("spark.sql.catalogImplementation", "hive") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.spark_catalog.type", "hive") \
        .config("spark.sql.catalog.spark_catalog.uri", "thrift://hive-metastore:9083") \
        .config("spark.sql.catalog.spark_catalog.warehouse", "s3a://weather-data/warehouse") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "rootuser") \
        .config("spark.hadoop.fs.s3a.secret.key", "rootpass123") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .getOrCreate()

    try:
        # Create Database
        print("Creating database 'weather_db'...")
        spark.sql("CREATE DATABASE IF NOT EXISTS spark_catalog.weather_db LOCATION 's3a://weather-data/warehouse/weather_db'")
        
        # Create Table
        print("Creating table 'hourly_aggregates'...")
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
        print("Warehouse initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing warehouse: {e}")
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    init_warehouse()