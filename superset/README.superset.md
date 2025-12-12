# 🔌 Connecting Superset to Trino

This guide explains how to add Trino as a database source in the Superset UI using the correct SQLAlchemy URI format.

## 📝 Prerequisites
* You must have **Admin** access to Superset.
* The Trino driver (`sqlalchemy-trino`) must already be installed in your Superset instance.

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