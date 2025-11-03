"""
Test script for weather data pipeline components.
"""
import json
import time
from datetime import datetime
from data_collector import get_weather_data, transform_weather_data
from mongodb_writer import MongoDBWriter
from config import Config

def test_data_collection():
    """Test weather data collection."""
    print("=" * 60)
    print("Testing Data Collection")
    print("=" * 60)
    
    if not Config.OPENWEATHER_API_KEY:
        print("ERROR: OPENWEATHER_API_KEY not set!")
        return False
    
    test_city = Config.CITIES[0] if Config.CITIES else "Hanoi"
    print(f"Testing with city: {test_city}")
    
    # Fetch data
    raw_data = get_weather_data(test_city, Config.OPENWEATHER_API_KEY)
    if not raw_data:
        print("FAILED: Could not fetch weather data")
        return False
    
    print("✓ Successfully fetched raw weather data")
    print(json.dumps(raw_data, indent=2))
    
    # Transform data
    transformed = transform_weather_data(raw_data, test_city)
    if not transformed:
        print("FAILED: Could not transform weather data")
        return False
    
    print("\n✓ Successfully transformed weather data")
    print(json.dumps(transformed, indent=2))
    
    return True

def test_mongodb_connection():
    """Test MongoDB connection."""
    print("\n" + "=" * 60)
    print("Testing MongoDB Connection")
    print("=" * 60)
    
    try:
        writer = MongoDBWriter()
        print("✓ Successfully connected to MongoDB")
        
        # Test write
        test_data = {
            "city": "TestCity",
            "temperature": 25.5,
            "humidity": 70,
            "weather": {"main": "Clear", "description": "clear sky"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = writer.upsert_latest_weather("TestCity", test_data)
        if result:
            print("✓ Successfully wrote test data to MongoDB")
            
            # Test read
            retrieved = writer.get_latest_weather("TestCity")
            if retrieved:
                print("✓ Successfully retrieved data from MongoDB")
                print(json.dumps(retrieved, indent=2, default=str))
            
            # Cleanup
            writer.delete_city_data("TestCity")
            print("✓ Cleaned up test data")
        else:
            print("FAILED: Could not write to MongoDB")
            return False
        
        writer.close()
        return True
        
    except Exception as e:
        print(f"FAILED: MongoDB connection error: {str(e)}")
        return False

def test_kafka_connection():
    """Test Kafka connection."""
    print("\n" + "=" * 60)
    print("Testing Kafka Connection")
    print("=" * 60)
    
    try:
        from kafka import KafkaProducer, KafkaConsumer
        import json
        
        # Test producer
        producer = KafkaProducer(
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=5000
        )
        
        # Send test message
        test_message = {
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Test message from pipeline test"
        }
        
        future = producer.send(Config.KAFKA_TOPIC, value=test_message)
        future.get(timeout=10)
        print("✓ Successfully published test message to Kafka")
        
        # Test consumer
        consumer = KafkaConsumer(
            Config.KAFKA_TOPIC,
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='latest',
            consumer_timeout_ms=5000,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        print("✓ Successfully connected to Kafka consumer")
        print("Note: Message consumption test skipped (timeout-based)")
        
        producer.close()
        consumer.close()
        return True
        
    except Exception as e:
        print(f"FAILED: Kafka connection error: {str(e)}")
        print("Make sure Kafka is running and accessible")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Weather Data Pipeline Test Suite")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    Config.print_config()
    
    results = {
        "Data Collection": test_data_collection(),
        "MongoDB Connection": test_mongodb_connection(),
        "Kafka Connection": test_kafka_connection()
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

