# Apache Spark Configuration

Apache Spark is the data processing engine that processes streaming weather data from Kafka and writes to Iceberg and MongoDB.

## Spark Services

### Spark Master
- **Port**: 8081 (Web UI), 7077 (Master port)
- **URL**: http://localhost:8081
- **Purpose**: Cluster manager that coordinates Spark workers and applications

### Spark Worker
- **Port**: 8082 (Web UI)
- **URL**: http://localhost:8082
- **Purpose**: Executes tasks assigned by Spark Master
- **Resources**: 2GB memory, 2 cores (configurable)

### Spark Streaming Application
- **Container**: `spark-streaming-app`
- **Purpose**: Runs the streaming processing application
- **Reads from**: Kafka
- **Writes to**: Iceberg (MinIO) and MongoDB

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

### Application Logs
```bash
# View Spark streaming app logs
docker-compose logs -f spark-streaming

# View Spark Master logs
docker-compose logs -f spark-master

# View Spark Worker logs
docker-compose logs -f spark-worker
```

## Configuration

Spark is configured to:
- **Connect to Kafka**: `kafka:29092`
- **Use Iceberg**: Via Hive Metastore at `hive-metastore:9083`
- **Store data**: MinIO at `s3a://weather-data/warehouse`
- **Write to MongoDB**: `mongodb:27017`

## What Spark Does

1. **Reads** weather data from Kafka topic `weather-data`
2. **Processes** data in real-time using Structured Streaming
3. **Aggregates** data into hourly windows
4. **Writes** aggregated data to Iceberg tables (for analytics)
5. **Writes** latest data per city to MongoDB (for serving)

## Scaling

To add more Spark workers:

```yaml
# In docker-compose.yml, duplicate spark-worker service
spark-worker-2:
  # ... same config as spark-worker
```

Or increase worker resources:
```yaml
environment:
  - SPARK_WORKER_MEMORY=4g
  - SPARK_WORKER_CORES=4
```

## Troubleshooting

### Spark app not connecting to Master
- Check Spark Master is running: `docker-compose ps spark-master`
- Verify network connectivity
- Check logs: `docker-compose logs spark-master`

### Out of memory errors
- Increase worker memory: `SPARK_WORKER_MEMORY=4g`
- Check Spark Master UI for resource allocation

### Kafka connection issues
- Verify Kafka is running: `docker-compose ps kafka`
- Check Kafka bootstrap servers: `kafka:29092`
- Verify topic exists: `weather-data`

## Resources

- [Spark Documentation](https://spark.apache.org/docs/latest/)
- [Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Spark on Docker](https://spark.apache.org/docs/latest/running-on-kubernetes.html)

