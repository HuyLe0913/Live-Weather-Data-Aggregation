# MongoDB Configuration (Hot Path / Serving Layer)

MongoDB is used as the **hot path (OLTP / serving layer)** in the weather data platform.  
It stores **low-latency, query-optimized snapshots** of processed weather data for real-time access and visualization.

MongoDB is **not** used for analytics or historical storage. Long-term and analytical queries are handled by **Apache Iceberg on MinIO**.

---

## Role in the Architecture

MongoDB serves as the **real-time access layer** between stream processing and visualization.

**Data flow:**

1. **Spark**  
   - Processes streaming and batch weather data  
   - Computes aggregations and latest-state metrics  
   - Writes latest-state results to MongoDB using upsert operations  

2. **MongoDB**  
   - Stores the **latest snapshot per city**  
   - Optimized for fast point lookups and dashboard queries  
   - Acts as the hot, mutable data store  

3. **Trino**  
   - Connects to MongoDB via the MongoDB connector  
   - Provides SQL access for BI tools  

4. **Apache Superset**  
   - Uses Trino as the query engine  
   - Visualizes near-real-time weather data from MongoDB  

---

## Why MongoDB for the Hot Path

MongoDB is chosen because it provides:

- Low-latency reads and writes
- Flexible schema for evolving weather payloads
- Native upsert semantics (ideal for “latest state” records)
- Easy integration with Trino and BI tools

This complements Iceberg, which is optimized for **analytical and historical queries**, not real-time serving.

---

## Data Model

### Document Characteristics

- **One document per city**
- Each write **overwrites the previous state**
- No append-only history is stored

Example document:

```json
{
  "city": "Hanoi",
  "temperature": 25.5,
  "humidity": 70,
  "avg_wind_speed": 3.2,
  "weather": {
    "main": "Clear",
    "description": "clear sky"
  },
  "timestamp": "2025-11-03T10:15:00Z",
  "updated_at": "2025-11-03T10:15:05Z"
}
```

### Write Path (Spark → MongoDB)

- Spark jobs compute aggregates and latest values
- Data is written using **upsert-by-city**
- Writes are **idempotent** and safe to retry

**Key characteristics:**
- No duplicate records
- Constant document count (bounded by number of cities)
- Optimized for frequent updates and low-latency writes

### Read Path (Trino → Superset)

- Trino connects to MongoDB using the **MongoDB connector**
- Superset queries MongoDB **indirectly via Trino**

**Typical queries:**
- Latest weather per city
- Filter by city
- Sort by timestamp or update time

MongoDB is **never queried directly** by Superset.

### Indexing Strategy

Indexes are created automatically at startup to support serving workloads:

- `city` — fast lookup by city
- `timestamp` — time-based filtering
- `(city, timestamp)` — common access pattern for latest data

These indexes ensure:
- Predictable query latency
- Efficient dashboard refreshes

---

## Configuration Files

- **MongoDB Writer**: `mongodb_writer.py`

**Environment Variables / Config:**
- `MONGODB_URI`
- `MONGODB_DATABASE`
- `MONGODB_COLLECTION`

- **Trino MongoDB Connector**: `trino/catalog/mongodb.properties`

---

## What MongoDB Is Not Used For

- ❌ Long-term historical storage
- ❌ Large analytical scans
- ❌ Complex joins or aggregations
- ❌ Time-travel queries

These use cases are handled by **Iceberg + Trino** instead.

---

## Troubleshooting

### MongoDB Connection Issues

**Symptoms**
- Spark job fails with MongoDB connection errors
- Trino queries fail with connector errors

**Checks**
- Verify `MONGODB_URI`, `MONGODB_DATABASE`, `MONGODB_COLLECTION`
- Ensure MongoDB container/service is running
- Check network/DNS resolution between Spark, Trino, and MongoDB
- Review MongoDB logs for authentication or connection failures

**Notes**
- Spark writes fail fast by design
- No data loss occurs because Kafka and Iceberg remain the source of truth

### Spark Write Failures

**Symptoms**
- Upserts not reflected in MongoDB
- Job retries without visible updates

**Checks**
- Confirm `upsert_by_city` logic is enabled
- Verify incoming records always contain a valid `city`
- Check MongoDB indexes were created successfully at startup
- Inspect Spark executor logs for write exceptions

**Recovery**
- Restart MongoDB if needed
- Re-run Spark job safely (idempotent upserts)

### Trino Cannot Query MongoDB

**Symptoms**
- Superset dashboards fail to load
- Trino reports connector or catalog errors

**Checks**
- Validate `trino/catalog/mongodb.properties`
- Ensure MongoDB is reachable from Trino
- Confirm database and collection names match MongoDB configuration
- Check Trino logs for connector initialization errors

### Data Appears Stale

**Symptoms**
- Dashboards show outdated weather data

**Checks**
- Confirm Spark jobs are running and completing successfully
- Verify `updated_at` or `timestamp` is being refreshed on each upsert
- Check Kafka ingestion and Iceberg pipeline health

**Notes**
- MongoDB reflects near-real-time state
- Historical correctness is guaranteed by Iceberg, not MongoDB

### Duplicate or Unexpected Records

**Symptoms**
- More documents than expected in the collection

**Checks**
- Verify upserts use `city` as the unique key
- Ensure no alternative write paths are inserting documents
- Confirm no manual inserts bypassing the writer utility

**Expected Behavior**
- Document count should remain bounded by number of cities

### When in Doubt

- Restart MongoDB and Trino (safe operation)
- Re-run Spark jobs (idempotent writes)
- Validate Iceberg tables for authoritative historical data
