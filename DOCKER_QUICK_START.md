# 🐳 Docker Quick Start - Run in 3 Steps

## Step 1: Create `.env` file

Create a `.env` file in the project root:

```env
OPENWEATHER_API_KEY=your_api_key_here
CITIES=Hanoi,Ho Chi Minh City,Da Nang
COLLECTION_INTERVAL=60
```

**Get your API key:** https://openweathermap.org/api

## Step 2: Start Everything

```bash
# Build and start all services (Kafka, MongoDB, MinIO, Data Collector)
docker-compose up -d --build
```

This will:
- ✅ Download required images
- ✅ Start Kafka (KRaft mode - no Zookeeper needed!)
- ✅ Start MongoDB
- ✅ Start MinIO (S3 storage)
- ✅ Build and start the data collector
- ✅ Start NiFi (data flow management)
- ✅ Start PostgreSQL (for Hive Metastore)
- ✅ Start Hive Metastore (metadata catalog)
- ✅ Start Iceberg REST Catalog (REST API for Iceberg)
- ✅ Start Spark Master (cluster manager)
- ✅ Start Spark Worker (task executor)
- ✅ Start Spark Streaming (data processing app)
- ✅ Start Trino (SQL query engine with Iceberg support)
- ✅ Start Superset (BI visualization)

## Step 3: Check It's Working

```bash
# View data collector logs
docker-compose logs -f data-collector
```

You should see weather data being collected and published to Kafka!

---

## 🔍 Verify Data

### Access Web UIs

| Service | URL | Credentials |
|---------|-----|-------------|
| **NiFi** | http://localhost:8080/nifi | admin / [see docker-compose.yml] |
| **Superset** | http://localhost:8088 | admin / admin |
| **Trino** | http://localhost:8090 | N/A |
| **MinIO Console** | http://localhost:9001 | rootuser / rootpass123 |
| **Hive Metastore** | localhost:9083 (Thrift) | N/A |
| **Iceberg REST** | http://localhost:8181 | N/A |
| **Spark Master** | http://localhost:8081 | N/A |
| **Spark Worker** | http://localhost:8082 | N/A |

### Check Kafka Messages
```bash
docker exec -it kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic weather-data \
  --from-beginning
```

### Check MongoDB Data
```bash
docker exec -it mongodb mongosh weather_db --eval "db.current_weather.find().pretty()"
```

### View All Services
```bash
docker-compose ps
```

---

## 📊 Useful Commands

```bash
# View logs
docker-compose logs -f data-collector

# Stop everything
docker-compose down

# Stop and delete all data
docker-compose down -v

# Restart data collector only
docker-compose restart data-collector

# Rebuild after code changes
docker-compose up -d --build data-collector
```

---

## 🛠️ Troubleshooting

### Services won't start
```bash
# Check what's wrong
docker-compose logs

# Check if ports are in use
netstat -ano | findstr :9092  # Windows
lsof -i :9092                  # Linux/Mac
```

### Data collector can't connect to Kafka
- Wait a few seconds after starting (Kafka needs time to initialize)
- Check logs: `docker-compose logs kafka`
- Verify network: `docker network ls`

### Missing API key
- Make sure `.env` file exists with `OPENWEATHER_API_KEY=...`
- Check it's in the same folder as `docker-compose.yml`

---

## 🌐 Service Access

After starting, you can access:

- **NiFi**: http://localhost:8080/nifi - Visual data flow management
- **Superset**: http://localhost:8088 - BI dashboards and charts
- **Trino**: http://localhost:8090 - SQL query interface
- **MinIO Console**: http://localhost:9001 - Object storage management

## 📝 Next Steps

1. **NiFi**: Import flow from `nifi/weather-data-flow.xml`
2. **Superset**: 
   - Connect to Trino: `trino://trino@trino:8080/hive/weather_db`
   - See `superset/SETUP_GUIDE.md` for details
3. **Trino**: Query Iceberg tables via SQL

That's it! 🎉 

For more details, see:
- `DOCKER_GUIDE.md` - Complete Docker documentation
- `docker-compose-full.md` - Full stack setup guide

