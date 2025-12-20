# Trino Configuration

This document describes how **Trino** is configured as the unified SQL query engine connecting **Hive Metastore + Iceberg**, **MongoDB**, and **Apache Superset**.

Trino acts as the central access layer.  
Neither Superset nor other consumers connect directly to Iceberg or MongoDB.

---

## System Role of Trino

Trino provides:

- A **single SQL endpoint**
- Access to **multiple storage systems**
- Schema-on-read querying
- Federation across OLAP and OLTP data sources

Superset

↓ (SQL)

Trino

├── Iceberg (via Hive Metastore + MinIO)

└── MongoDB

---

## Trino Catalogs

Trino uses **catalogs** to connect to different backends.

Each backend is isolated but queryable through SQL.

trino/catalog/
├── iceberg.properties
├── hive.properties
└── mongodb.properties

---

## Connection Steps

1.  Log in to Superset.
2.  Navigate to **Settings** (top right icon) → **Database Connections**.
3.  Click the **+ Database** button.
4.  In the "Supported Databases" list, select **Trino**.
5.  In the **SQLAlchemy URI** field, enter the connection string using the format below.

---

## SQLAlchemy URI Format

The connection string follows this standard syntax:

```text
trino://{user}:{password}@{host}:{port}/{catalog}
```

### Example:

- trino://admin@trino:8080/iceberg

- trino://admin@trino:8080/mongodb