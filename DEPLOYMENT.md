# Deployment Guide

This guide walks you through deploying the Live Weather Data Aggregation System.

## Prerequisites

1. **Kubernetes Cluster**: Minikube or any Kubernetes cluster
2. **Helm**: Package manager for Kubernetes
3. **kubectl**: Kubernetes command-line tool
4. **OpenWeatherMap API Key**: Get one from [OpenWeatherMap](https://openweathermap.org/api)

## Step 1: Set Up Kubernetes Infrastructure

Follow the setup scripts in the `scripts/` folder:

```bash
# On Linux
bash scripts/kuber_setup.txt

# Then deploy services
bash scripts/kuber_services.txt
```

Or manually run:

```bash
# Start minikube
minikube start

# Create namespaces
kubectl create namespace ingestion
kubectl create namespace processing
kubectl create namespace storage
kubectl create namespace query
kubectl create namespace viz

# Deploy services using Helm
helm install nifi cetic/nifi -n ingestion
helm install kafka oci://registry-1.docker.io/bitnamicharts/kafka -n ingestion
helm install spark oci://registry-1.docker.io/bitnamicharts/spark -n processing
helm install minio oci://registry-1.docker.io/bitnamicharts/minio -n storage \
  --set rootUser=rootuser,rootPassword=rootpass123
helm install mongodb oci://registry-1.docker.io/bitnamicharts/mongodb -n storage
helm repo add heva-helm-charts https://hevaweb.github.io/heva-helm-charts/
helm install hive-metastore heva-helm-charts/hive-metastore -n storage
helm repo add trino https://trinodb.github.io/charts/
helm install trino trino/trino -n query
helm install superset oci://registry-1.docker.io/bitnamicharts/superset -n viz
```

## Step 2: Build Docker Images

Build the Docker images for the data collector and Spark application:

```bash
# Build data collector image
docker build -f Dockerfile.data_collector -t weather-data-collector:latest .

# Build Spark application image
docker build -f Dockerfile.spark_app -t weather-spark-app:latest .
```

## Step 3: Configure Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env and add your OpenWeatherMap API key
```

For Kubernetes deployment, create secrets:

```bash
# Create API key secret
kubectl create secret generic weather-api-secret \
  --from-literal=api-key=YOUR_API_KEY \
  -n ingestion

# Create MinIO secret
kubectl create secret generic minio-secret \
  --from-literal=access-key=rootuser \
  --from-literal=secret-key=rootpass123 \
  -n storage
```

## Step 4: Deploy Applications

### Option A: Local Development

1. **Run Data Collector**:
   ```bash
   python data_collector.py
   ```

2. **Run Spark Streaming**:
   ```bash
   spark-submit \
     --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.mongodb.spark:mongo-spark-connector_2.12:3.0.1 \
     spark_streaming_app.py
   ```

### Option B: Kubernetes Deployment

1. **Deploy Data Collector**:
   ```bash
   kubectl apply -f k8s/data-collector-deployment.yaml
   ```

2. **Deploy Spark Application**:
   ```bash
   kubectl apply -f k8s/spark-app-deployment.yaml
   ```

## Step 5: Initialize Iceberg Tables

Connect to Trino or Spark SQL and run:

```bash
# Using Spark SQL
spark-sql -f setup_tables.sql

# Or using Trino CLI
trino --execute "$(cat setup_tables.sql)"
```

## Step 6: Verify Deployment

### Check Data Collector Logs
```bash
kubectl logs -f deployment/weather-data-collector -n ingestion
```

### Check Spark Application Logs
```bash
kubectl logs -f job/weather-spark-streaming -n processing
```

### Verify Kafka Topics
```bash
kubectl exec -it kafka-0 -n ingestion -- kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Query Data in Trino
```bash
# Connect to Trino
kubectl port-forward svc/trino -n query 8080:8080

# Query hourly aggregates
trino --server localhost:8080 --catalog spark_catalog --execute \
  "SELECT * FROM weather_db.hourly_aggregates LIMIT 10"
```

### Check MongoDB Data
```bash
# Connect to MongoDB
kubectl exec -it mongodb-0 -n storage -- mongosh

# Query current weather
use weather_db
db.current_weather.find().pretty()
```

## Step 7: Access Visualization (Superset)

```bash
# Port forward Superset
kubectl port-forward svc/superset -n viz 8088:8088

# Access at http://localhost:8088
# Default credentials: admin/admin
```

## Troubleshooting

### Kafka Connection Issues
- Verify Kafka service is running: `kubectl get pods -n ingestion`
- Check Kafka bootstrap servers configuration
- Verify network policies allow communication

### Spark Application Errors
- Check Spark logs for detailed error messages
- Verify all required JAR packages are included
- Ensure Hive Metastore is accessible

### MinIO Connection Issues
- Verify MinIO service is running: `kubectl get pods -n storage`
- Check S3 endpoint configuration
- Verify access keys are correct

### MongoDB Connection Issues
- Verify MongoDB service is running: `kubectl get pods -n storage`
- Check connection string format
- Verify network connectivity

## Scaling

To scale the data collector:

```bash
kubectl scale deployment weather-data-collector --replicas=3 -n ingestion
```

## Monitoring

Monitor the system using:

```bash
# Check pod status
kubectl get pods --all-namespaces

# Check resource usage
kubectl top pods --all-namespaces
```

## Cleanup

To remove all deployments:

```bash
kubectl delete -f k8s/
helm uninstall nifi -n ingestion
helm uninstall kafka -n ingestion
helm uninstall spark -n processing
helm uninstall minio -n storage
helm uninstall mongodb -n storage
helm uninstall hive-metastore -n storage
helm uninstall trino -n query
helm uninstall superset -n viz
```

