### NiFi Workflow & Saving Changes

This section describes the data flow and the essential process for saving any modifications.

#### 📦 NiFi Flow Description

The flow is a pipeline that automates weather data collection:

1.  **Scheduler (`GenerateFlowFile`):**:
Triggers the entire flow on a fixed schedule (e.g., every 5 minutes).
Generate a flow file containing a string list of all city names separated by new line characters.
Acts as the entry point of the pipeline and controls ingestion frequency.

2.  **Split (`SplitText`):** 
Splits the list into individual FlowFiles, one for each city.

3.  **Extract (`ExtractText`):** 
Reads the city name from the content and saves it as an attribute (e.g., `city = "Hanoi"`).

4.  **Fetch (`InvokeHTTP`):** 
Uses the `city` attribute to call the OpenWeatherMap API and get the raw JSON data.

5.  **Transform (`JoltTransformJSON` / `UpdateAttribute`):** 
- Normalizes and cleans the raw API response 
- Adds a processing `timestamp` for downstream consistency

6.  **Publish (`PublishKafka`):** 
Publishes the final JSON payload to the `weather-data` Kafka topic.  
The `city` attribute is used as the Kafka message key to guarantee partitioning consistency.

---

#### 💾 How to Save Flow Changes

NiFi stores flow state inside the container. Any changes must be explicitly exported to persist them across restarts or deployments.

**1. Stop the Flow**
In the NiFi UI, select all processors (Ctrl+A) and click the **Stop** icon (■).

**2. Copy the Flow**
Run this command on your local machine to copy the modified flow out of the container:

```bash
docker cp nifi:/opt/nifi/nifi-current/conf/flow.json.gz ./nifi/