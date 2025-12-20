# Apache Spark Configuration

Apache Spark is the **central processing engine** in the platform.  
It consumes streaming weather events from Kafka, performs real-time transformations and aggregations, and writes results to **two different storage layers** optimized for different workloads:

- **Iceberg on MinIO** → analytical / historical (OLAP)
- **MongoDB** → serving / near-real-time dashboards (OLTP)

Spark does not store data itself; it acts purely as a compute layer.

---

## Spark Services

### Spark Master
- **Port**: 8081 (Web UI), 7077 (Master port)
- **URL**: http://localhost:8081
- **Purpose**: 
  - Acts as the cluster manager
  - Schedules applications and distributes work to Spark workers
  - Tracks worker health and resource availability

### Spark Worker
- **Port**: 8082 (Web UI)
- **URL**: http://localhost:8082
- **Purpose**: Executes tasks assigned by Spark Master
- **Resources**: 2GB memory, 2 cores (configurable)

### Spark Streaming Application
- **Container**: `spark-streaming-app`
- **Purpose**: Runs the Structured Streaming job defined in `spark_streaming_app.py`
- **Reads from**: Kafka
- **Writes to**:
  - Apache Iceberg (on MinIO) for analytics
  - MongoDB for serving and dashboards

---

## Architecture

```
Kafka (weather-data topic)
    ↓
Spark Streaming App
    ↓
Spark Master (coordinates)
    ↓
Spark Worker (executes)
    ├─> Iceberg Tables (MinIO)
    └─> MongoDB (latest weather)
```

---

## Monitoring

### Spark Master UI
Access at http://localhost:8081 to see:
- Running applications
- Worker status
- Resource usage

### Spark Worker UI
Access at http://localhost:8082 to see:
- Executor status
- Task execution
- Resource metrics

---

## Configuration

Spark is configured to:
- **Connect to Kafka**: `kafka:29092`
- **Use Iceberg**: Via Hive Metastore at `hive-metastore:9083`
- **Store data**: MinIO at `s3a://weather-data/warehouse`
- **Write to MongoDB**: `mongodb:27017`

---

## What Spark Does
The `spark_streaming_app.py` executes the following pipeline:

## 1. Ingestion & Parsing

* **Source**: Connects to the Kafka broker (`kafka:29092`) and subscribes to the `weather-data` topic.

* **Deserialization**: Parses JSON payloads using a strict schema defined in `schemas.py`.

* **Event Time**: Extracts the `event_timestamp` from the raw data to handle out-of-order events, ensuring analytics are based on when the weather *happened*, not when the data *arrived*.

## 2. Watermarking & Aggregation (OLAP Path)

Spark maintains a running state to aggregate data for historical analysis.

* **Watermarking (10 minutes)**: Spark waits for late data up to 10 minutes. Events older than this threshold are dropped to keep the state size manageable.

* **Tumbling Windows (1 Hour)**: Data is grouped into non-overlapping 1-hour windows (e.g., `10:00-11:00`, `11:00-12:00`).

* **Aggregation**: Calculates statistics per City:

  * `avg/max/min temperature`

  * `avg_humidity`, `avg_pressure`

  * `record_count`

## 3. Dual-Path Routing (Lambda Architecture)

The stream is split into two independent output sinks:

* **Path A: Cold Storage (Analytics)**

  * **Destination**: **Apache Iceberg** tables in **MinIO (S3)**.

  * **Format**: Parquet files tracked by Hive Metastore.

  * **Partitioning**: Physically partitioned by `city`.

  * **Behavior**: **Append Only**. Data is committed only after the window closes (1 hour + 10 mins watermark delay).

* **Path B: Hot Storage (Serving)**

  * **Destination**: **MongoDB** (`weather_db.current_weather`).

  * **Mechanism**: Uses `foreachBatch` to perform fast upserts.

  * **Behavior**: **Real-time**. Updates are visible immediately as batches are processed.

