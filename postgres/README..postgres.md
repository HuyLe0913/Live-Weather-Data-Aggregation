# PostgreSQL – Hive Metastore & Iceberg Catalog

This PostgreSQL instance is used **exclusively for metadata storage** in the data platform.  
It does **not** store any actual weather data. All analytical data lives in **MinIO (S3)** and is managed by **Apache Iceberg**.

---

## Role in the Architecture

PostgreSQL serves as the **metadata backbone** for:

- **Hive Metastore**
- **Apache Iceberg catalogs**

It enables consistent table discovery and schema management across Spark, Trino, and other compute engines.

---

## What PostgreSQL Stores

### Hive Metastore Metadata
Stored in the `metastore` database:

- Database definitions
- Table schemas
- Column definitions and types
- Partition metadata
- Iceberg table references

### Iceberg Catalog Metadata
Stored in the `iceberg_catalog` database:

- Iceberg namespace information
- Table identifiers
- Snapshot and version references
- Catalog-level metadata

Both databases are initialized automatically on first startup.

⚠️ **No actual data files** (Parquet, manifests, etc.) are stored in PostgreSQL.

---

## Initialization

PostgreSQL is initialized using a Docker entrypoint script:

- Creates the `iceberg_catalog` database
- Grants privileges to the `hive` user
- Relies on `POSTGRES_DB` to create the `metastore` database automatically

Initialization runs **only on first startup** (empty volume).

---

## Connection Details

- **Host (Docker network)**: `postgres`
- **Port**: `5432`
- **User**: `hive`
- **Used by**: Hive Metastore

Credentials are supplied via environment variables and referenced by Hive Metastore configuration.

---

## How Other Services Use PostgreSQL

### Hive Metastore
- Connects via JDBC
- Reads/writes metadata only
- Exposes metadata via Thrift (port 9083)

### Spark
- Never connects to PostgreSQL directly
- Accesses metadata through Hive Metastore

### Trino
- Never connects to PostgreSQL directly
- Queries metadata through Hive Metastore

---

## Failure & Recovery

If PostgreSQL is unavailable:

- Hive Metastore cannot start
- Spark and Trino cannot resolve tables
- No data loss occurs (data is stored in MinIO)

Recovery steps:

1. Restart PostgreSQL container
2. Restart Hive Metastore
3. Restart dependent services if needed

Metadata remains intact as long as the PostgreSQL volume is preserved.

---

## What PostgreSQL Is Not Used For

❌ Storing weather data  
❌ Analytical queries  
❌ Time-series storage  
❌ High-throughput writes  
❌ Dashboard queries  

These responsibilities belong to:

- **Kafka** – ingestion
- **Iceberg + MinIO** – analytical storage
- **MongoDB** – hot serving layer
- **Trino** – query engine
