"""
Utility functions for weather data processing pipeline.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional

def validate_weather_data(data: Dict[str, Any]) -> bool:
    """
    Validate weather data structure.
    
    Args:
        data: Weather data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["timestamp", "city", "temperature", "humidity", "weather"]
    return all(field in data for field in required_fields)

def format_timestamp(timestamp_str: Optional[str] = None) -> str:
    """
    Format timestamp to ISO format.
    
    Args:
        timestamp_str: Optional timestamp string. If None, uses current time.
        
    Returns:
        ISO formatted timestamp string
    """
    if timestamp_str:
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.isoformat()
        except:
            return datetime.utcnow().isoformat()
    return datetime.utcnow().isoformat()

def extract_city_from_key(key: str) -> str:
    """
    Extract city name from Kafka key.
    
    Args:
        key: Kafka message key
        
    Returns:
        City name
    """
    return key.strip() if key else "Unknown"

def calculate_heat_index(temperature: float, humidity: float) -> Optional[float]:
    """
    Calculate heat index (feels-like temperature).
    
    Args:
        temperature: Temperature in Celsius
        humidity: Relative humidity percentage
        
    Returns:
        Heat index value or None if calculation not applicable
    """
    if temperature < 27 or humidity < 40:
        return None
    
    # Simplified heat index calculation for Celsius
    # Full calculation would use Fahrenheit and convert
    temp_f = (temperature * 9/5) + 32
    hi = (-42.379 + 
          2.04901523 * temp_f + 
          10.14333127 * humidity - 
          0.22475541 * temp_f * humidity - 
          6.83783e-3 * temp_f**2 - 
          5.481717e-2 * humidity**2 + 
          1.22874e-3 * temp_f**2 * humidity + 
          8.5282e-4 * temp_f * humidity**2 - 
          1.99e-6 * temp_f**2 * humidity**2)
    
    return (hi - 32) * 5/9  # Convert back to Celsius

def get_weather_condition_description(weather_code: str) -> str:
    """
    Get human-readable weather condition description.
    
    Args:
        weather_code: Weather condition code
        
    Returns:
        Human-readable description
    """
    descriptions = {
        "Clear": "Clear sky",
        "Clouds": "Cloudy",
        "Rain": "Rainy",
        "Drizzle": "Light rain",
        "Thunderstorm": "Thunderstorm",
        "Snow": "Snowy",
        "Mist": "Misty",
        "Fog": "Foggy"
    }
    return descriptions.get(weather_code, "Unknown")

def create_aggregation_key(city: str, country: str, window_start: datetime) -> str:
    """
    Create a unique key for aggregations.
    
    Args:
        city: City name
        country: Country code
        window_start: Window start timestamp
        
    Returns:
        Unique aggregation key
    """
    window_str = window_start.strftime("%Y-%m-%d-%H")
    return f"{city}_{country}_{window_str}"

def log_processing_metrics(
    records_processed: int,
    records_failed: int,
    processing_time_ms: float,
    source: str
):
    """
    Log processing metrics.
    
    Args:
        records_processed: Number of successfully processed records
        records_failed: Number of failed records
        processing_time_ms: Processing time in milliseconds
        source: Data source identifier
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "metrics": {
            "records_processed": records_processed,
            "records_failed": records_failed,
            "processing_time_ms": processing_time_ms,
            "success_rate": records_processed / (records_processed + records_failed) if (records_processed + records_failed) > 0 else 0
        }
    }
    print(json.dumps(log_entry))

