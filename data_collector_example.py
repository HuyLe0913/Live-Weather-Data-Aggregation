import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
CITY = os.environ.get("CITY", "Hanoi")
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

def main():
    print(f"[{datetime.now()}] Collecting weather data for {CITY}...")
    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()
        print(data)
        print(f"Temperature: {data['main']['temp']}°C")
        print(f"Humidity: {data['main']['humidity']}%")
        print(f"Weather: {data['weather'][0]['description']}")
    else:
        print("Failed to fetch data:", response.text)

if __name__ == "__main__":
    main()