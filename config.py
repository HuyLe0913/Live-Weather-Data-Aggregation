"""
Configuration management for weather data pipeline.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Central configuration class."""
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
        "KAFKA_BOOTSTRAP_SERVERS", 
        "kafka.kafka.svc.cluster.local:9092"
    )
    KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "weather-data")
    KAFKA_CONSUMER_GROUP = os.environ.get("KAFKA_CONSUMER_GROUP", "weather-spark-consumer")
    
    # OpenWeatherMap API Configuration
    OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
    CITIES = os.environ.get("CITIES", "Hanoi,Ho Chi Minh City,Da Nang").split(",")
    COLLECTION_INTERVAL = int(os.environ.get("COLLECTION_INTERVAL", "60"))
    
    # MinIO/S3 Configuration
    MINIO_ENDPOINT = os.environ.get(
        "MINIO_ENDPOINT", 
        "http://minio.storage.svc.cluster.local:9000"
    )
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "rootuser")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "rootpass123")
    MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "weather-data")
    WAREHOUSE_PATH = f"s3a://{MINIO_BUCKET}/warehouse"
    
    # Hive Metastore Configuration
    HIVE_METASTORE_URI = os.environ.get(
        "HIVE_METASTORE_URI", 
        "thrift://hive-metastore.storage.svc.cluster.local:9083"
    )
    
    # MongoDB Configuration
    MONGODB_URI = os.environ.get(
        "MONGODB_URI", 
        "mongodb://mongodb.storage.svc.cluster.local:27017"
    )
    MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "weather_db")
    MONGODB_COLLECTION = os.environ.get("MONGODB_COLLECTION", "current_weather")
    
    # Spark Configuration
    SPARK_APP_NAME = os.environ.get("SPARK_APP_NAME", "WeatherDataStreaming")
    SPARK_MASTER = os.environ.get("SPARK_MASTER", "local[*]")
    # Streaming Configuration
    STREAMING_CHECKPOINT_LOCATION = os.environ.get(
        "STREAMING_CHECKPOINT_LOCATION",
        "/tmp/spark-checkpoints"
    )
    STREAMING_TRIGGER_INTERVAL = os.environ.get("STREAMING_TRIGGER_INTERVAL", "1 minute")
    WATERMARK_DELAY_THRESHOLD = os.environ.get("WATERMARK_DELAY_THRESHOLD", "10 minutes")
    WINDOW_DURATION = os.environ.get("WINDOW_DURATION", "1 hour")
    
    # Iceberg Configuration
    ICEBERG_CATALOG_NAME = os.environ.get("ICEBERG_CATALOG_NAME", "spark_catalog")
    ICEBERG_DATABASE = os.environ.get("ICEBERG_DATABASE", "weather_db")
    ICEBERG_TABLE_AGGREGATES = os.environ.get(
        "ICEBERG_TABLE_AGGREGATES", 
        "hourly_aggregates"
    )
    
    @classmethod
    def get_spark_config(cls) -> dict:
        """Get Spark configuration dictionary."""
        return {
            "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            "spark.sql.catalog.spark_catalog": "org.apache.iceberg.spark.SparkCatalog",
            "spark.sql.catalog.spark_catalog.type": "hive",
            "spark.sql.catalog.spark_catalog.uri": cls.HIVE_METASTORE_URI,
            "spark.sql.catalog.spark_catalog.warehouse": cls.WAREHOUSE_PATH,
            "spark.sql.catalog.spark_catalog.io-impl": "org.apache.iceberg.aws.s3.S3FileIO",
            "spark.sql.catalog.spark_catalog.s3.endpoint": cls.MINIO_ENDPOINT,
            "spark.sql.catalog.spark_catalog.s3.access-key-id": cls.MINIO_ACCESS_KEY,
            "spark.sql.catalog.spark_catalog.s3.secret-access-key": cls.MINIO_SECRET_KEY,
            "spark.sql.catalog.spark_catalog.s3.path-style-access": "true",
            "spark.hadoop.fs.s3a.endpoint": cls.MINIO_ENDPOINT,
            "spark.hadoop.fs.s3a.access.key": cls.MINIO_ACCESS_KEY,
            "spark.hadoop.fs.s3a.secret.key": cls.MINIO_SECRET_KEY,
            "spark.hadoop.fs.s3a.path.style.access": "true",
            "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
            "spark.hadoop.fs.s3a.connection.ssl.enabled": "false",
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true"
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.OPENWEATHER_API_KEY:
            print("WARNING: OPENWEATHER_API_KEY not set")
            return False
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (without secrets)."""
        print("=" * 60)
        print("Configuration:")
        print("=" * 60)
        print(f"Kafka Bootstrap Servers: {cls.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"Kafka Topic: {cls.KAFKA_TOPIC}")
        print(f"Cities: {', '.join(cls.CITIES)}")
        print(f"MinIO Endpoint: {cls.MINIO_ENDPOINT}")
        print(f"MinIO Bucket: {cls.MINIO_BUCKET}")
        print(f"MongoDB URI: {cls.MONGODB_URI}")
        print(f"MongoDB Database: {cls.MONGODB_DATABASE}")
        print(f"Hive Metastore URI: {cls.HIVE_METASTORE_URI}")
        print(f"Spark App Name: {cls.SPARK_APP_NAME}")
        print(f"Streaming Trigger: {cls.STREAMING_TRIGGER_INTERVAL}")
        print("=" * 60)

