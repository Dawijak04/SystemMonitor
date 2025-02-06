from flask import Flask, jsonify, render_template
from config_loader import load_config
from sys_metrics import get_system_metrics
from logger_config import setup_logging
from metrics.local_metrics import LocalMetrics
from metrics.external_api_metrics import WeatherMetrics
import json
import sys
import threading
import time
import os
from datetime import datetime, timedelta


app = Flask(__name__)
app.config.update(load_config())

#config = ConfigManager()
config = load_config()

# Get API key from environment variable
WEATHER_API_KEY = config["WEATHER_API_KEY"]

# Move logger initialization before thread creation
logger = setup_logging(config)

# Initialize WeatherMetrics
weather_metrics = WeatherMetrics(
    api_key=WEATHER_API_KEY, logger=logger
)

@app.route('/')
def hello_world():
    logger.info("Loading hello world")
    return render_template('home.html')

@app.route('/local-metrics')
def local_metrics():
    return render_template('local_metrics.html')

@app.route('/api-metrics')
def api_metrics():
    return render_template('api_metrics.html')

@app.route('/api/external-metrics')
def api_external_metrics():
    try:
        if not os.path.exists("external_metrics.json"):
            logger.error("external_metrics.json does not exist")
            return jsonify({"error": "No metrics data available"}), 404
            
        with open("external_metrics.json", 'r') as f:
            metrics = json.load(f)
            
        logger.debug(f"Serving cached weather data")
        
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error reading external metrics: {str(e)}")
        return jsonify({"error": "Unable to read metrics"}), 500

@app.route('/api/local-metrics')
def api_local_metrics():
    try:
        with open("local_metrics.json", 'r') as f:
            metrics = json.load(f)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error reading local metrics: {str(e)}")
        return jsonify({"error": "Unable to read metrics"}), 500

def metrics_collector():
    local_metrics = LocalMetrics(logger)
    weather_metrics = WeatherMetrics(logger, config["WEATHER_API_KEY"])
    last_weather_update = datetime.min
    
    while True:
        try:
            # Collect local metrics
            local_data = local_metrics.get_metrics()
            with open("local_metrics.json", 'w') as f:
                json.dump(local_data, f)
            
            # Update weather data every 10 minutes
            now = datetime.now()
            if now - last_weather_update > timedelta(minutes=10):
                logger.info("Fetching new weather data")
                try:
                    # Get weather data and log it
                    london_weather = weather_metrics.get_weather_data("London")
                    paris_weather = weather_metrics.get_weather_data("Paris")
                    berlin_weather = weather_metrics.get_weather_data("Berlin")
                    
                    logger.info(f"London weather: {london_weather}")
                    logger.info(f"Paris weather: {paris_weather}")
                    logger.info(f"Berlin weather: {berlin_weather}")
                    
                    external_data = {
                        "weather": {
                            "london": london_weather,
                            "paris": paris_weather,
                            "berlin": berlin_weather
                        },
                        "last_updated": now.isoformat()
                    }
                    
                    with open("external_metrics.json", 'w') as f:
                        json.dump(external_data, f)
                    last_weather_update = now
                    logger.info("Weather data updated successfully")
                except Exception as e:
                    logger.error(f"Error updating weather data: {str(e)}")
            
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in metrics collector: {str(e)}")
            time.sleep(5)

# Start the metrics collector in a background thread
collector_thread = threading.Thread(target=metrics_collector, daemon=True)
collector_thread.start()

if __name__ == '__main__':
    logger.info("Starting the application")
    # logger.warning("Warning message")
    # logger.error("Error message")
    # logger.critical("Critical message")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
    sys.exit(0)
