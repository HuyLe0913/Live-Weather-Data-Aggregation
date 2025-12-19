# Hive Metastore Configuration

This directory contains Hive Metastore configuration for the weather data pipeline.
In this pipeline, Hive Metastore is used exclusively as the metadata catalog for Apache Iceberg tables stored on MinIO (S3). Hive provide a shared metadata layer so that multiple engines can consistently access the same Iceberg tables.
Specifically:
- Iceberg table data and metadata files are stored in MinIO (S3)

- Hive Metastore stores logical metadata and references to those Iceberg tables

- Compute/Query engines can use Hive Metastore to discover and resolve Iceberg tables

## Configuration

The `metastore-site.xml` file configures:
- PostgreSQL database connection for metadata storage
- MinIO (S3) warehouse directory (physical location where table data and Iceberg metadata files are stored)
- Thrift server settings (network interface used by external services such as Spark and Trino)
- Iceberg table format support

## Service Details

**Port:** 9083 (Thrift protocol)
The Thrift service exposes Hive Metastore APIs over TCP.

**Connection String:**
- From Docker network: `thrift://hive-metastore:9083`
- From host: `thrift://localhost:9083`

## Database Schema

Hive Metastore uses PostgreSQL to store:
- Table metadata (table names, locations, properties, ...)
- Database schemas
- Partition information
- Column types and statistics
PostgreSQL does not store actual data files or Iceberg manifest files as those are stored in the warehouse (MinIO/S3) referenced by the metadata.

## Initialization

On first run, Hive Metastore will automatically:
1. Connect to PostgreSQL database
2. Create required schema tables
3. Initialize metadata structures

## Usage

Services that connect to Hive Metastore:
- **Spark**: Uses metastore to discover Iceberg tables
- **Trino**: Queries metadata via Hive connector
- **Apache Iceberg**: Stores table metadata here (actual Iceberg metadata files live in the MinIO warehouse)

## Troubleshooting

### Schema initialization fails
- Wait for PostgreSQL to be fully ready before starting Hive Metastore
- Check PostgreSQL logs: `docker-compose logs postgres`
- Verify database credentials in `metastore-site.xml`

### Connection refused
- Check Hive Metastore is running: `docker-compose ps hive-metastore`
- Check logs: `docker-compose logs hive-metastore`
- Verify port 9083 is accessible and correctly exposed

### S3/MinIO connection issues
- Ensure MinIO is running: `docker-compose ps minio`
- Verify S3 endpoint in `metastore-site.xml`
- Check access keys are correct
- Ensure all clients use the same S3 endpoint and path-style access settings

