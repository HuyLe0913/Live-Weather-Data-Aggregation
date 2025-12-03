### NiFi Workflow & Saving Changes

This section describes the data flow and the essential process for saving any modifications.

#### 📦 NiFi Flow Description

The flow is a pipeline that automates weather data collection:

1.  **Scheduler (`GenerateFlowFile`):** Triggers the entire flow on a fixed schedule (e.g., every 5 minutes).
2.  **Create List (`ReplaceText`):** Generates a FlowFile containing a list of target cities (Hanoi, Da Nang, etc.).
3.  **Split (`SplitText`):** Splits the list into individual FlowFiles, one for each city.
4.  **Extract (`ExtractText`):** Reads the city name from the content and saves it as an attribute (e.g., `city = "Hanoi"`).
5.  **Fetch (`InvokeHTTP`):** Uses the `city` attribute to call the OpenWeatherMap API and get the raw JSON data.
6.  **Transform (`JoltTransformJSON` / `UpdateAttribute`):** Cleans the raw JSON and adds a new `timestamp` field.
7.  **Publish (`PublishKafka`):** Sends the final, clean JSON to the `weather-data` Kafka topic, using the `city` as the message key.

---

#### 💾 How to Save Flow Changes

**1. Stop the Flow**
In the NiFi UI, select all processors (Ctrl+A) and click the **Stop** icon (■).

**2. Copy the Flow**
Run this command on your local machine to copy the modified flow out of the container:

```bash
docker cp nifi:/opt/nifi/nifi-current/conf/flow.json.gz ./nifi/