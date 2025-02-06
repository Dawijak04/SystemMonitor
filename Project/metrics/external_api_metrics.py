from datetime import datetime, timedelta
import random
import requests

class WeatherMetrics:
    def __init__(self, logger, api_key):
        self.logger = logger
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.cache = {
            'data': None,
            'last_update': None
        }

    def get_weather_data(self, city="London"):
        """Get weather data from OpenWeatherMap"""
        try:
            self.logger.info(f"Fetching weather data for {city}")
            
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric"
            }
            
            # Log the request URL and API key (remove in production)
            self.logger.info(f"Request URL: {self.base_url}")
            self.logger.info(f"Using API key: {self.api_key}")
            
            response = requests.get(self.base_url, params=params)
            self.logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"API error: {response.text}")
                raise Exception(f"API returned status code {response.status_code}")
                
            data = response.json()
            self.logger.info(f"Raw API response: {data}")
            
            weather_metrics = {
                "city": city,
                "temperature": round(data["main"]["temp"], 1),
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "feels_like": round(data["main"]["feels_like"], 1),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Processed weather metrics for {city}: {weather_metrics}")
            return weather_metrics
            
        except Exception as e:
            self.logger.error(f"Error getting weather data for {city}: {str(e)}")
            return {
                "city": city,
                "temperature": 0,
                "humidity": 0,
                "description": "Error fetching data",
                "feels_like": 0,
                "timestamp": datetime.now().isoformat()
            }

# params = {
#     "q": "London",
#     "appid": '0db44c1ef277fc786c843762e5d066ba',
#     "units": "metric"  # for Celsius
# }

# response = requests.get("http://api.openweathermap.org/data/2.5/weather", params=params)
# data = response.json()
# print(data)
