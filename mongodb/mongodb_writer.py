"""
MongoDB Writer Utility

Purpose:
- Writes processed weather data to MongoDB
- Optimized for the OLTP / serving layer
- Stores the *latest state per city* rather than historical time series
"""

from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, BulkWriteError
from datetime import datetime
from typing import List, Dict, Any, Union
import json
from config import Config

class MongoDBWriter:
    """
    Utility class responsible for all MongoDB write and read operations:
    - One document per city (latest snapshot)
    - Fast reads for APIs / dashboards
    - Upsert-based writes to avoid duplicates
    """
    
    def __init__(self, uri: str = None, database: str = None, collection: str = None):
        """
        Initialize MongoDB writer.
        
        Args:
            uri: MongoDB connection URI
            database: Database name
            collection: Collection name

        If arguments are not provided, values are read from Config.
        """

        # Resolve configuration (explicit args override Config defaults)
        self.uri = uri or Config.MONGODB_URI
        self.database_name = database or Config.MONGODB_DATABASE
        self.collection_name = collection or Config.MONGODB_COLLECTION

        # Runtime objects
        self.client = None
        self.db = None
        self.collection = None

        # Initialize connection and indexes
        self._connect()
        self._create_indexes()
    
    def _connect(self):
        """Establish MongoDB connection."""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000) # Uses a short timeout to fail fast if MongoDB is unavailable
            # Test connection
            # Pings the server to verify connectivity
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            print(f"Connected to MongoDB: {self.database_name}.{self.collection_name}")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def _create_indexes(self):
        """Create indexes to support low-latency serving queries."""
        try:
            # Index on city for fast lookups
            self.collection.create_index("city", unique=False)
            # Index on timestamp for time-based queries
            self.collection.create_index("timestamp", unique=False)
            # Compound index for city + timestamp
            self.collection.create_index([("city", 1), ("timestamp", -1)])
            print("MongoDB indexes created")
        except Exception as e:
            print(f"Error creating indexes: {str(e)}")
    
    def upsert_latest_weather(self, city: str, weather_data: Dict[str, Any]) -> bool:
        """
        Upsert latest weather data for a city.
        
        Args:
            city: City name (unique key)
            weather_data: Weather data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure city is in the document
            weather_data["city"] = city
            weather_data["updated_at"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"city": city},
                {"$set": weather_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            print(f"Error upserting weather data for {city}: {str(e)}")
            return False
    
    def bulk_upsert_weather(self, weather_records: List[Dict[str, Any]]) -> bool:
        """
        Bulk upsert weather data for multiple cities.
        
        Args:
            weather_records: List of weather data dictionaries with 'city' key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            operations = []
            for record in weather_records:
                city = record.get("city", "Unknown")
                record["updated_at"] = datetime.utcnow()
                
                operations.append(
                    UpdateOne(
                        {"city": city},
                        {"$set": record},
                        upsert=True
                    )
                )
            
            if operations:
                result = self.collection.bulk_write(operations, ordered=False)
                print(f"Bulk upserted {result.modified_count + result.upserted_count} records")
                return result.acknowledged
            return True
        except BulkWriteError as e:
            print(f"Bulk write error: {str(e)}")
            return False
        except Exception as e:
            print(f"Error in bulk upsert: {str(e)}")
            return False
    
    def get_latest_weather(self, city: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get latest weather data.
        
        Args:
            city: Optional city name. If None, returns all cities.
            
        Returns:
            Weather data dictionary or list of dictionaries
        """
        try:
            query = {"city": city} if city else {}
            # Sort by updated_at descending to get latest record
            result = self.collection.find_one(query, sort=[("updated_at", -1)])
            return result if result else {}
        except Exception as e:
            print(f"Error getting latest weather: {str(e)}")
            return {} if city else []
    
    def get_all_cities_weather(self) -> List[Dict[str, Any]]:
        """
        Get latest weather for all cities.
        
        Returns:
            List of weather data dictionaries
        """
        try:
            # Get distinct cities
            cities = self.collection.distinct("city")
            results = []
            
            for city in cities:
                weather = self.get_latest_weather(city)
                if weather:
                    results.append(weather)
            
            return results
        except Exception as e:
            print(f"Error getting all cities weather: {str(e)}")
            return []
    
    def delete_city_data(self, city: str) -> bool:
        """
        Delete weather data for a city.
        
        Args:
            city: City name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.delete_many({"city": city})
            print(f"Deleted {result.deleted_count} records for {city}")
            return result.acknowledged
        except Exception as e:
            print(f"Error deleting city data: {str(e)}")
            return False
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

def main():
    """
    Standalone test entry point.

    Verifies:
    - MongoDB connectivity
    - Upsert logic
    - Read-after-write correctness
    """
    writer = MongoDBWriter()
    
    # Test data
    test_data = {
        "city": "Hanoi",
        "temperature": 25.5,
        "humidity": 70,
        "weather": {"main": "Clear", "description": "clear sky"},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Test upsert
    result = writer.upsert_latest_weather("Hanoi", test_data)
    print(f"Upsert result: {result}")
    
    # Test retrieval
    weather = writer.get_latest_weather("Hanoi")
    print(f"Retrieved weather: {json.dumps(weather, indent=2, default=str)}")
    
    writer.close()

if __name__ == "__main__":
    main()

