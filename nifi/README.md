# NiFi Weather Data Flow Configuration

This directory contains the Apache NiFi flow configuration for weather data ingestion.

## Files

- `weather-data-flow.xml`: NiFi flow definition XML that defines the data ingestion pipeline

## Flow Overview

The NiFi flow performs the following steps:

1. **Generate Cities**: Creates flow files for each city to monitor
2. **Fetch Weather Data**: Calls OpenWeatherMap API for each city
3. **Evaluate JSON**: Extracts key fields from the API response
4. **Transform Data**: Transforms data to standardized format using JOLT
5. **Publish to Kafka**: Sends transformed data to Kafka topic

## Importing into NiFi

### Method 1: Via NiFi UI

1. Access NiFi UI (usually at `http://nifi.ingestion.svc.cluster.local:8080/nifi`)
2. Right-click on the canvas → **Upload Template** or **Import Flow**
3. Select `weather-data-flow.xml`
4. Configure the processors with your API key and Kafka connection details

### Method 2: Via NiFi REST API

```bash
# Get NiFi service URL
kubectl get svc -n ingestion | grep nifi

# Port forward
kubectl port-forward svc/nifi -n ingestion 8080:8080

# Upload flow via REST API
curl -X POST http://localhost:8080/nifi-api/process-groups/{root-group-id}/process-groups/import \
  -H "Content-Type: application/xml" \
  --data-binary @weather-data-flow.xml
```

### Method 3: Manual Setup in NiFi UI

1. Add processors from the toolbar:
   - **GenerateFlowFile**: Generate list of cities
   - **InvokeHTTP**: Fetch weather data
   - **EvaluateJsonPath**: Extract JSON fields
   - **JoltTransformJSON**: Transform data format
   - **PublishKafkaRecord**: Send to Kafka

2. Configure each processor:
   - **InvokeHTTP**: Set URL to `http://api.openweathermap.org/data/2.5/weather?q=${filename}&appid=${OPENWEATHER_API_KEY}&units=metric`
   - **PublishKafkaRecord**: Set brokers to `kafka.ingestion.svc.cluster.local:9092` and topic to `weather-data`

3. Connect processors in sequence

## Environment Variables

Create a NiFi controller service for environment variables:

1. Go to **Controller Settings** → **Controller Services**
2. Add **Variable Registry** service
3. Add variable: `OPENWEATHER_API_KEY` with your API key

## Scheduling

Configure scheduling for each processor:
- **GenerateFlowFile**: Schedule to run every 60 seconds (or desired interval)
- **InvokeHTTP**: Run on schedule or triggered by upstream
- **PublishKafkaRecord**: Run on schedule or triggered by upstream

## Monitoring

Monitor the flow in NiFi UI:
- View data flow metrics
- Check processor status
- Review flowfile attributes
- Monitor queue sizes

## Alternative: Using Python Data Collector

Instead of NiFi, you can use the Python `data_collector.py` script which performs the same function and publishes directly to Kafka.

