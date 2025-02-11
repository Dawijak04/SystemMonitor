import os
import json
import time
from datetime import datetime
from metrics.local_metrics import LocalMetrics
from metrics.external_api_metrics import WeatherMetrics
from logger_config import setup_logging

# Load config first
from config_loader import load_config
config = load_config()

# Setup logging with config
logger = setup_logging(config)

# Setup paths
METRICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metrics_data')
LOCAL_METRICS_PATH = os.path.join(METRICS_DIR, 'local_metrics.json')
EXTERNAL_METRICS_PATH = os.path.join(METRICS_DIR, 'external_metrics.json')

def collect_metrics():
    try:
        # Ensure metrics directory exists
        os.makedirs(METRICS_DIR, exist_ok=True)
        
        # Collect local metrics
        local_metrics = LocalMetrics(logger)
        local_data = local_metrics.get_metrics()
        with open(LOCAL_METRICS_PATH, 'w') as f:
            json.dump(local_data, f)
        logger.info("Local metrics collected successfully")
        
        # Collect weather metrics
        weather_metrics = WeatherMetrics(
            logger=logger,
            api_key=config['WEATHER_API_KEY']
        )
        
        # Get weather for multiple cities
        london_weather = weather_metrics.get_weather_data("London")
        paris_weather = weather_metrics.get_weather_data("Paris")
        berlin_weather = weather_metrics.get_weather_data("Berlin")
        
        # Structure the data as expected by the frontend
        external_data = {
            "weather": {
                "london": london_weather,
                "paris": paris_weather,
                "berlin": berlin_weather
            },
            "last_updated": datetime.now().isoformat()
        }
        
        with open(EXTERNAL_METRICS_PATH, 'w') as f:
            json.dump(external_data, f)
        logger.info("Weather metrics collected successfully")
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {str(e)}")

if __name__ == '__main__':
    collect_metrics()