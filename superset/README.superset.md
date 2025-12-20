# 🔌 Connecting Superset to Trino

This guide explains how to add **Trino** as a database source in the Superset UI and clarifies how to set up **Trino connections** to provide access to **both Iceberg and MongoDB** through separate catalogs.

Superset never connects directly to Iceberg or MongoDB.  
All queries are routed through Trino.

---

## 📝 Prerequisites

* You must have **Admin** access to Superset.
* The Trino driver (`sqlalchemy-trino`) must already be installed in your Superset instance.
* Trino must be running and reachable from Superset.
* Trino catalogs for **Iceberg** and **MongoDB** must already be configured.

---

## 🧠 Architecture Overview
Superset
↓ (SQL)
Trino
├── iceberg catalog → Iceberg tables on MinIO (historical / OLAP)
└── mongodb catalog → MongoDB collections (hot / serving)

---

## 🚀 Connection Steps

1.  Log in to Superset.
2.  Navigate to **Settings** (top right icon) → **Database Connections**.
3.  Click the **+ Database** button.
4.  In the "Supported Databases" list, select **Trino**.
5.  In the **SQLAlchemy URI** field, enter the connection string using the format below.

---

## 🔗 SQLAlchemy URI Format

The connection string follows this standard syntax:

```text
trino://{user}:{password}@{host}:{port}/{catalog}
```

### Example:

- trino://admin@trino:8080/iceberg

- trino://admin@trino:8080/mongodb