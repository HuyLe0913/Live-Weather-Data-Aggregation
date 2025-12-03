-- SQL script to set up Iceberg tables for weather data
-- This can be run in Trino or Spark SQL

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS spark_catalog.weather_db;

USE spark_catalog.weather_db;

-- Hourly aggregated weather data table
CREATE TABLE IF NOT EXISTS hourly_aggregates (
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
);

-- Raw weather data table (optional, for historical analysis)
CREATE TABLE IF NOT EXISTS raw_weather_data (
    timestamp TIMESTAMP,
    city STRING,
    country STRING,
    latitude DOUBLE,
    longitude DOUBLE,
    temperature DOUBLE,
    feels_like DOUBLE,
    pressure INT,
    humidity INT,
    temp_min DOUBLE,
    temp_max DOUBLE,
    visibility INT,
    wind_speed DOUBLE,
    wind_direction DOUBLE,
    clouds INT,
    weather_main STRING,
    weather_description STRING,
    sunrise BIGINT,
    sunset BIGINT,
    timezone INT,
    kafka_timestamp TIMESTAMP
) USING iceberg
PARTITIONED BY (days(timestamp), city)
TBLPROPERTIES (
    'write.format.default' = 'parquet',
    'write.parquet.compression-codec' = 'snappy'
);

-- Daily aggregated weather data table (for longer-term analysis)
CREATE TABLE IF NOT EXISTS daily_aggregates (
    date DATE,
    city STRING,
    country STRING,
    avg_temperature DOUBLE,
    max_temperature DOUBLE,
    min_temperature DOUBLE,
    avg_humidity DOUBLE,
    avg_pressure DOUBLE,
    avg_wind_speed DOUBLE,
    max_wind_speed DOUBLE,
    record_count BIGINT,
    processed_at TIMESTAMP
) USING iceberg
PARTITIONED BY (months(date), city)
TBLPROPERTIES (
    'write.format.default' = 'parquet',
    'write.parquet.compression-codec' = 'snappy'
);

-- View for easy querying
CREATE OR REPLACE VIEW latest_weather_by_city AS
SELECT 
    city,
    country,
    avg_temperature,
    max_temperature,
    min_temperature,
    avg_humidity,
    window_end as last_updated
FROM hourly_aggregates
WHERE window_end = (
    SELECT MAX(window_end) 
    FROM hourly_aggregates h2 
    WHERE h2.city = hourly_aggregates.city
);

