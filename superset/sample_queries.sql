-- Sample SQL Queries for Superset Dashboards
-- These queries can be used in Superset's SQL Lab or as custom charts

-- ============================================
-- 1. Latest Weather by City
-- ============================================
SELECT 
    city,
    country,
    avg_temperature,
    max_temperature,
    min_temperature,
    avg_humidity,
    avg_pressure,
    avg_wind_speed,
    window_end as last_updated
FROM weather_db.hourly_aggregates
WHERE window_end = (
    SELECT MAX(window_end) 
    FROM weather_db.hourly_aggregates h2 
    WHERE h2.city = hourly_aggregates.city
)
ORDER BY city;

-- ============================================
-- 2. Temperature Trends (Last 24 Hours)
-- ============================================
SELECT 
    window_start as time,
    city,
    avg_temperature,
    max_temperature,
    min_temperature
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
ORDER BY window_start DESC, city;

-- ============================================
-- 3. Daily Average Temperature
-- ============================================
SELECT 
    DATE(window_start) as date,
    city,
    AVG(avg_temperature) as daily_avg_temp,
    MAX(max_temperature) as daily_max_temp,
    MIN(min_temperature) as daily_min_temp,
    AVG(avg_humidity) as daily_avg_humidity
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY DATE(window_start), city
ORDER BY date DESC, city;

-- ============================================
-- 4. City Weather Comparison (Current Hour)
-- ============================================
SELECT 
    city,
    country,
    avg_temperature as temperature,
    avg_humidity as humidity,
    avg_pressure as pressure,
    avg_wind_speed as wind_speed,
    record_count,
    window_start,
    window_end
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '1' HOUR
ORDER BY avg_temperature DESC;

-- ============================================
-- 5. Temperature Range by City (Last Week)
-- ============================================
SELECT 
    city,
    MIN(min_temperature) as lowest_temp,
    MAX(max_temperature) as highest_temp,
    AVG(avg_temperature) as avg_temp,
    MAX(max_temperature) - MIN(min_temperature) as temp_range
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY city
ORDER BY temp_range DESC;

-- ============================================
-- 6. Hourly Temperature Heatmap Data
-- ============================================
SELECT 
    EXTRACT(HOUR FROM window_start) as hour,
    city,
    AVG(avg_temperature) as avg_temp,
    AVG(avg_humidity) as avg_humidity
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
GROUP BY EXTRACT(HOUR FROM window_start), city
ORDER BY hour, city;

-- ============================================
-- 7. Weather Statistics Summary
-- ============================================
SELECT 
    city,
    COUNT(*) as total_records,
    MIN(window_start) as first_record,
    MAX(window_end) as last_record,
    AVG(avg_temperature) as overall_avg_temp,
    MIN(min_temperature) as all_time_min,
    MAX(max_temperature) as all_time_max,
    AVG(avg_humidity) as overall_avg_humidity,
    AVG(avg_wind_speed) as overall_avg_wind
FROM weather_db.hourly_aggregates
GROUP BY city
ORDER BY city;

-- ============================================
-- 8. Temperature Distribution
-- ============================================
SELECT 
    CASE 
        WHEN avg_temperature < 15 THEN 'Cold (<15°C)'
        WHEN avg_temperature < 25 THEN 'Moderate (15-25°C)'
        WHEN avg_temperature < 30 THEN 'Warm (25-30°C)'
        ELSE 'Hot (>30°C)'
    END as temp_category,
    city,
    COUNT(*) as count
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY temp_category, city
ORDER BY temp_category, city;

-- ============================================
-- 9. Wind Speed Analysis
-- ============================================
SELECT 
    window_start as time,
    city,
    avg_wind_speed,
    CASE 
        WHEN avg_wind_speed < 5 THEN 'Calm'
        WHEN avg_wind_speed < 15 THEN 'Light'
        WHEN avg_wind_speed < 25 THEN 'Moderate'
        ELSE 'Strong'
    END as wind_category
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
ORDER BY window_start DESC, avg_wind_speed DESC;

-- ============================================
-- 10. Daily Weather Summary
-- ============================================
SELECT 
    DATE(window_start) as date,
    city,
    AVG(avg_temperature) as avg_temp,
    MAX(max_temperature) as max_temp,
    MIN(min_temperature) as min_temp,
    AVG(avg_humidity) as avg_humidity,
    AVG(avg_wind_speed) as avg_wind,
    SUM(record_count) as total_measurements
FROM weather_db.hourly_aggregates
WHERE window_start >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
GROUP BY DATE(window_start), city
ORDER BY date DESC, city;

