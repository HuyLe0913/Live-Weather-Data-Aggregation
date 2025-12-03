# Superset Configuration

This directory contains configuration and guides for setting up Apache Superset to visualize weather data.

## Files

- `SETUP_GUIDE.md`: Complete step-by-step guide for setting up Superset
- `sample_queries.sql`: Ready-to-use SQL queries for Superset dashboards

## Quick Start

1. **Access Superset:**
   ```bash
   kubectl port-forward svc/superset -n viz 8088:8088
   ```
   Open: `http://localhost:8088`

2. **Default Login:**
   - Username: `admin`
   - Password: `admin`

3. **Add Database Connection:**
   - Go to Data → Databases
   - Add new database
   - Type: **Trino**
   - SQLAlchemy URI: `trino://trino@trino.query.svc.cluster.local:8080/hive/weather_db`

4. **Import Sample Queries:**
   - Use queries from `sample_queries.sql` in SQL Lab
   - Create charts from these queries
   - Build dashboards

## Recommended Dashboards

1. **Real-time Weather Dashboard**
   - Latest weather by city
   - Temperature trends
   - Humidity and pressure gauges

2. **Historical Analysis Dashboard**
   - Daily/weekly trends
   - Temperature distribution
   - Wind speed analysis

3. **City Comparison Dashboard**
   - Side-by-side city comparison
   - Heatmaps
   - Statistical summaries

## Next Steps

See `SETUP_GUIDE.md` for detailed instructions on:
- Configuring database connections
- Creating charts and visualizations
- Building dashboards
- Troubleshooting common issues

