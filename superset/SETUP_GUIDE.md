# Apache Superset Setup Guide

This guide walks you through setting up Apache Superset to visualize weather data from Trino.

## Prerequisites

### Option A: Docker Compose (Recommended for Local Development)

1. Superset running in Docker (via `docker-compose.yml`)
2. Trino running and accessible
3. Iceberg tables created and populated (via `setup_tables.sql`)

### Option B: Kubernetes

1. Superset deployed in Kubernetes (via Helm from `scripts/kuber_services.txt`)
2. Trino running and accessible
3. Iceberg tables created and populated (via `setup_tables.sql`)

## Step 1: Access Superset

### Docker Compose

```bash
# Superset is already running in docker-compose
# Access at: http://localhost:8088
```

### Kubernetes

```bash
# Get Superset service URL
kubectl get svc -n viz | grep superset

# Port forward to access Superset UI
kubectl port-forward svc/superset -n viz 8088:8088
```

**Access Superset at:** `http://localhost:8088`

**Default Credentials:**
- Username: `admin`
- Password: `admin` (change on first login)

## Step 2: Configure Database Connection

1. **Navigate to Data → Databases**
2. **Click "+ Database"**
3. **Select "Trino"** as database type
4. **Fill in connection details:**

   **For Docker Compose:**
   ```
   trino://trino@trino:8080/hive/weather_db
   ```
   Note: Use service name `trino` (not localhost) when connecting from Superset container

   **For Kubernetes:**
   ```
   trino://trino@trino.query.svc.cluster.local:8080/hive/weather_db
   ```

   **With authentication:**
   ```
   trino://username:password@trino:8080/hive/weather_db
   ```

   **Alternative format:**
   ```
   trino+http://trino@trino:8080/hive/weather_db
   ```

5. **Test Connection** and save

## Step 3: Register Tables

1. **Navigate to Data → Datasets**
2. **Click "+ Dataset"**
3. **Select your database** (Trino connection)
4. **Select schema:** `weather_db`
5. **Select tables:**
   - `hourly_aggregates`
   - `raw_weather_data` (if created)
   - `daily_aggregates` (if created)
6. **Click "Add"**

## Step 4: Create Charts

### Chart 1: Hourly Temperature by City

1. **Navigate to Charts → + Chart**
2. **Select Dataset:** `hourly_aggregates`
3. **Visualization Type:** Line Chart
4. **Time Column:** `window_start`
5. **Metrics:** `avg_temperature` (AVG)
6. **Group By:** `city`
7. **Filters:** Optional - filter by date range
8. **Save** as "Hourly Temperature by City"

### Chart 2: Temperature Range by City

1. **Create new chart**
2. **Dataset:** `hourly_aggregates`
3. **Visualization Type:** Bar Chart
4. **Metrics:** 
   - `max_temperature` (MAX)
   - `min_temperature` (MIN)
5. **Group By:** `city`
6. **Save** as "Temperature Range by City"

### Chart 3: Humidity Heatmap

1. **Create new chart**
2. **Dataset:** `hourly_aggregates`
3. **Visualization Type:** Heatmap
4. **X-axis:** `window_start` (granularity: Hour)
5. **Y-axis:** `city`
6. **Metric:** `avg_humidity` (AVG)
7. **Save** as "Humidity Heatmap"

### Chart 4: Wind Speed Over Time

1. **Create new chart**
2. **Dataset:** `hourly_aggregates`
3. **Visualization Type:** Area Chart
4. **Time Column:** `window_start`
5. **Metrics:** `avg_wind_speed` (AVG)
6. **Group By:** `city`
7. **Save** as "Wind Speed Over Time"

### Chart 5: City Comparison Table

1. **Create new chart**
2. **Dataset:** `hourly_aggregates`
3. **Visualization Type:** Table
4. **Columns:**
   - `city`
   - `avg_temperature`
   - `max_temperature`
   - `min_temperature`
   - `avg_humidity`
   - `avg_wind_speed`
   - `window_end`
5. **Filters:** Latest window only
6. **Save** as "City Weather Comparison"

## Step 5: Create Dashboard

1. **Navigate to Dashboards → + Dashboard**
2. **Name:** "Weather Data Dashboard"
3. **Add Charts:**
   - Drag and drop the charts created above
   - Arrange them in a grid layout
4. **Auto-refresh:** Set to refresh every 5 minutes (optional)
5. **Save Dashboard**

## Step 6: SQL Queries (Optional)

You can also create SQL-based charts:

### Query: Latest Weather by City

```sql
SELECT 
    city,
    country,
    avg_temperature,
    max_temperature,
    min_temperature,
    avg_humidity,
    avg_wind_speed,
    window_end as last_updated
FROM weather_db.hourly_aggregates
WHERE window_end = (
    SELECT MAX(window_end) 
    FROM weather_db.hourly_aggregates h2 
    WHERE h2.city = hourly_aggregates.city
)
ORDER BY city
```

### Query: Temperature Trends

```sql
SELECT 
    window_start,
    city,
    avg_temperature,
    max_temperature,
    min_temperature
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
ORDER BY window_start DESC, city
```

## Step 7: Configure Trino Connection Parameters

If you need custom Trino settings, add query parameters:

```
trino://trino@trino.query.svc.cluster.local:8080/hive/weather_db?
  protocol=https&
  catalog=hive&
  schema=weather_db
```

## Troubleshooting

### Connection Issues

- **Verify Trino is running:**
  ```bash
  kubectl get pods -n query | grep trino
  ```

- **Check Trino logs:**
  ```bash
  kubectl logs -f trino-0 -n query
  ```

- **Test Trino connection:**
  ```bash
  kubectl port-forward svc/trino -n query 8080:8080
  curl http://localhost:8080/v1/info
  ```

### Table Not Found

- Ensure Iceberg tables are created: Run `setup_tables.sql`
- Verify schema name: Should be `weather_db`
- Check table exists:
  ```sql
  SHOW TABLES FROM weather_db;
  ```

### Query Timeout

- Increase query timeout in Superset database settings
- Check Trino resource limits
- Optimize queries with appropriate filters

## Advanced: Custom Visualizations

You can create custom visualizations using:
- **SQL Lab**: Write custom SQL queries
- **Semantic Layer**: Create metrics and calculated columns
- **Plugins**: Install additional visualization plugins

## Security

1. **Change default admin password**
2. **Create roles and permissions**
3. **Enable authentication** (LDAP, OAuth, etc.)
4. **Configure SSL/TLS** for production

## Resources

- [Superset Documentation](https://superset.apache.org/docs/)
- [Trino Connector Documentation](https://trino.io/docs/current/connector.html)
- [Superset SQL Lab Guide](https://superset.apache.org/docs/using-superset/sqllab/)

