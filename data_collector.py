"""
Weather Data Collector
Collects weather data from OpenWeatherMap API and publishes to Kafka.
This can be used standalone or as a reference for NiFi data flow.
"""
import requests
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError

load_dotenv()

# Configuration
API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
CITIES = os.environ.get("CITIES", "Hanoi,Ho Chi Minh City,Da Nang").split(",")
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "weather-data")
COLLECTION_INTERVAL = int(os.environ.get("COLLECTION_INTERVAL", "60"))  # seconds

def get_weather_data(city, api_key):
    """Fetch weather data from OpenWeatherMap API."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch data for {city}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching weather data for {city}: {str(e)}")
        return None

def transform_weather_data(raw_data, city):
    """Transform raw API response to standardized format."""
    if not raw_data:
        return None
    
    try:
        transformed = {
            "timestamp": datetime.utcnow().isoformat(),
            "city": city,
            "country": raw_data.get("sys", {}).get("country", ""),
            "coordinates": {
                "latitude": raw_data.get("coord", {}).get("lat"),
                "longitude": raw_data.get("coord", {}).get("lon")
            },
            "temperature": raw_data.get("main", {}).get("temp"),
            "feels_like": raw_data.get("main", {}).get("feels_like"),
            "pressure": raw_data.get("main", {}).get("pressure"),
            "humidity": raw_data.get("main", {}).get("humidity"),
            "temp_min": raw_data.get("main", {}).get("temp_min"),
            "temp_max": raw_data.get("main", {}).get("temp_max"),
            "visibility": raw_data.get("visibility"),
            "wind": {
                "speed": raw_data.get("wind", {}).get("speed"),
                "direction": raw_data.get("wind", {}).get("deg"),
                "gust": raw_data.get("wind", {}).get("gust")
            },
            "clouds": raw_data.get("clouds", {}).get("all"),
            "weather": {
                "main": raw_data.get("weather", [{}])[0].get("main", ""),
                "description": raw_data.get("weather", [{}])[0].get("description", ""),
                "icon": raw_data.get("weather", [{}])[0].get("icon", "")
            },
            "sunrise": raw_data.get("sys", {}).get("sunrise"),
            "sunset": raw_data.get("sys", {}).get("sunset"),
            "timezone": raw_data.get("timezone")
        }
        return transformed
    except Exception as e:
        print(f"Error transforming data for {city}: {str(e)}")
        return None

def publish_to_kafka(producer, topic, data, city):
    """Publish weather data to Kafka topic."""
    try:
        key = city.encode('utf-8')
        value = json.dumps(data).encode('utf-8')
        future = producer.send(topic, key=key, value=value)
        future.get(timeout=10)
        print(f"[{datetime.now()}] Published weather data for {city} to topic {topic}")
        return True
    except KafkaError as e:
        print(f"Error publishing to Kafka for {city}: {str(e)}")
        return False

def main():
    """Main function to continuously collect and publish weather data."""
    if not API_KEY:
        print("ERROR: OPENWEATHER_API_KEY not set in environment variables!")
        return
    
    print(f"Starting Weather Data Collector...")
    print(f"Kafka Bootstrap Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Kafka Topic: {KAFKA_TOPIC}")
    print(f"Cities: {', '.join(CITIES)}")
    print(f"Collection Interval: {COLLECTION_INTERVAL} seconds")
    print("-" * 60)
    
    # Initialize Kafka producer
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            key_serializer=lambda k: k if isinstance(k, bytes) else k.encode('utf-8') if k else None,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Kafka producer initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize Kafka producer: {str(e)}")
        print("Running in print-only mode (not publishing to Kafka)")
        producer = None
    
    # Main collection loop
    try:
        while True:
            for city in CITIES:
                city = city.strip()
                print(f"\n[{datetime.now()}] Collecting weather data for {city}...")
                
                # Fetch weather data
                raw_data = get_weather_data(city, API_KEY)
                
                if raw_data:
                    # Transform data
                    transformed_data = transform_weather_data(raw_data, city)
                    
                    if transformed_data:
                        # Print to console
                        print(f"  Temperature: {transformed_data['temperature']}°C")
                        print(f"  Humidity: {transformed_data['humidity']}%")
                        print(f"  Weather: {transformed_data['weather']['description']}")
                        
                        # Publish to Kafka
                        if producer:
                            publish_to_kafka(producer, KAFKA_TOPIC, transformed_data, city)
                        else:
                            print(f"  [DEBUG] Data: {json.dumps(transformed_data, indent=2)}")
                
                # Small delay between cities
                time.sleep(2)
            
            print(f"\n[{datetime.now()}] Waiting {COLLECTION_INTERVAL} seconds before next collection cycle...")
            time.sleep(COLLECTION_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        if producer:
            producer.close()
            print("Kafka producer closed")

if __name__ == "__main__":
    main()

