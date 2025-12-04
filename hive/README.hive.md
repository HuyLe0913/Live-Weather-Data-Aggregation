# Hive Metastore Configuration

This directory contains Hive Metastore configuration for the weather data pipeline.

## Configuration

The `metastore-site.xml` file configures:
- PostgreSQL database connection for metadata storage
- MinIO (S3) warehouse directory
- Thrift server settings
- Iceberg table format support

## Service Details

**Port:** 9083 (Thrift protocol)

**Connection String:**
- From Docker network: `thrift://hive-metastore:9083`
- From host: `thrift://localhost:9083`

## Database Schema

Hive Metastore uses PostgreSQL to store:
- Table metadata
- Database schemas
- Partition information
- Column types and statistics

## Initialization

On first run, Hive Metastore will automatically:
1. Connect to PostgreSQL database
2. Create required schema tables
3. Initialize metadata structures

## Usage

Services that connect to Hive Metastore:
- **Spark**: Uses metastore to discover Iceberg tables
- **Trino**: Queries metadata via Hive connector
- **Apache Iceberg**: Stores table metadata here

## Troubleshooting

### Schema initialization fails
- Wait for PostgreSQL to be fully ready
- Check PostgreSQL logs: `docker-compose logs postgres`
- Verify database credentials in `metastore-site.xml`

### Connection refused
- Check Hive Metastore is running: `docker-compose ps hive-metastore`
- Check logs: `docker-compose logs hive-metastore`
- Verify port 9083 is accessible

### S3/MinIO connection issues
- Ensure MinIO is running: `docker-compose ps minio`
- Verify S3 endpoint in `metastore-site.xml`
- Check access keys are correct

