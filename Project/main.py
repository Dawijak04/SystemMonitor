from flask import Flask, jsonify, render_template
from config_loader import load_config
from sys_metrics import get_system_metrics
from logger_config import setup_logging
from metrics.local_metrics import LocalMetrics
from metrics.external_api_metrics import WeatherMetrics
import json
import sys
import os
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)
app.config.update(load_config())

# Load configuration
config = load_config()

# Get API key from config
WEATHER_API_KEY = config["WEATHER_API_KEY"]

# Setup logging
logger = setup_logging(config)

# Setup metrics paths
METRICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metrics_data')
LOCAL_METRICS_PATH = os.path.join(METRICS_DIR, 'local_metrics.json')
EXTERNAL_METRICS_PATH = os.path.join(METRICS_DIR, 'external_metrics.json')

# Add these constants after the existing path definitions
CACHE_DURATION = timedelta(minutes=5)  # Adjust cache duration as needed

# Initialize WeatherMetrics
weather_metrics = WeatherMetrics(
    logger=logger,
    api_key=WEATHER_API_KEY
)

def is_cache_valid(file_path):
    """Check if cache file exists and is within valid timeframe"""
    if not os.path.exists(file_path):
        return False
    
    file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    return datetime.now() - file_modified_time < CACHE_DURATION

@app.route('/')
def hello_world():
    logger.info("Loading hello world")
    welcome_message = config.get("welcome_message", "Hello World")
    return render_template('home.html', welcome_message=welcome_message)

@app.route('/local-metrics')
def local_metrics():
    return render_template('local_metrics.html')

@app.route('/api-metrics')
def api_metrics():
    return render_template('api_metrics.html')

@app.route('/api/external-metrics')
def api_external_metrics():
    try:
        if not is_cache_valid(EXTERNAL_METRICS_PATH):
            # Cache invalid or missing, trigger collection
            return trigger_metrics_collection()
            
        with open(EXTERNAL_METRICS_PATH, 'r') as f:
            metrics = json.load(f)
            
        logger.debug("Serving cached weather data")
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error reading external metrics: {str(e)}")
        return jsonify({"error": "Unable to read metrics"}), 500

@app.route('/api/local-metrics')
def api_local_metrics():
    try:
        if not is_cache_valid(LOCAL_METRICS_PATH):
            # Cache invalid or missing, trigger collection
            return trigger_metrics_collection()
            
        with open(LOCAL_METRICS_PATH, 'r') as f:
            metrics = json.load(f)
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error reading local metrics: {str(e)}")
        return jsonify({"error": "Unable to read metrics"}), 500

@app.route('/api/collect-metrics')
def trigger_metrics_collection():
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
        london_weather = weather_metrics.get_weather_data("London")
        paris_weather = weather_metrics.get_weather_data("Paris")
        berlin_weather = weather_metrics.get_weather_data("Berlin")
        
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
        
        return jsonify({"status": "success", "message": "Metrics collected successfully"})
    except Exception as e:
        logger.error(f"Error collecting metrics: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting the application")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False  # Set to False for production
    )
    sys.exit(0)
