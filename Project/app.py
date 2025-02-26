from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
#from models import LocalMetrics, WeatherMetrics, init_db
from models import init_db
import json
import secrets
from datetime import datetime, timedelta
from database_manager import DatabaseOperations

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Initialize database and create session maker
engine = init_db()
Session = sessionmaker(bind=engine)

def get_latest_metrics():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        
        # Get both local and weather metrics
        local_data = db_ops.get_latest_local_metrics()
        weather_data = db_ops.get_latest_weather_metrics()

        print("Debug - Latest Local:", local_data)  # Debug log
        print("Debug - Latest Weather:", weather_data)  # Debug log

        metrics = {}
        
        if local_data and 'local' in local_data:
            metrics['local'] = {
                'battery_percent': local_data['local']['battery_percent'],
                'memory_usage': local_data['local']['memory_usage']
            }
            
        if weather_data and 'weather' in weather_data:
            metrics['weather'] = {
                'temperature': weather_data['weather']['temperature'],
                'humidity': weather_data['weather']['humidity'],
                'description': weather_data['weather']['description'],
                'city': weather_data['weather']['city']
            }

        print("Debug - Returning metrics:", metrics) 
        return metrics if metrics else None
        
    finally:
        session.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/local')
def local():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        initial_data = db_ops.get_latest_local_metrics()
        return render_template('local.html', initial_data=initial_data)
    finally:
        session.close()

@app.route('/weather')
def weather():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        initial_data = db_ops.get_latest_weather_metrics()
        return render_template('weather.html', initial_data=initial_data)
    finally:
        session.close()

@app.route('/metrics', methods=['POST'])
def handle_metrics():
    metrics = request.json
    print("Received metrics update:", metrics)
    session = Session()

    try:
        db_ops = DatabaseOperations(session)
        success, message = db_ops.store_metrics(metrics)
        
        if success:
            print("Metrics saved to database")
            return jsonify({"status": "success", "message": message}), 200
        else:
            print(f"Error saving metrics: {message}")
            return jsonify({"status": "error", "message": message}), 500
            
    except Exception as e:
        print(f"Error saving metrics: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/api/history/local')
def local_history():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        latest = db_ops.get_latest_local_metrics()
        
        if latest and 'local' in latest:
            return {
                'timestamps': [latest['local']['timestamp']],
                'battery': [float(latest['local']['battery_percent'])],
                'memory': [float(latest['local']['memory_usage'])],
                'last_updated': latest['local']['timestamp']
            }

        return {
            'timestamps': [],
            'battery': [],
            'memory': [],
            'last_updated': None
        }
    finally:
        session.close()

@app.route('/api/history/weather')
def weather_history():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        latest = db_ops.get_latest_weather_metrics()
        
        if latest and 'weather' in latest:
            return {
                'timestamps': [latest['weather']['timestamp']],
                'temperature': [float(latest['weather']['temperature'])],
                'humidity': [float(latest['weather']['humidity'])],
                'description': [latest['weather']['description']],
                'city': [latest['weather']['city']],
                'last_updated': latest['weather']['timestamp']
            }
        
        return {
            'timestamps': [],
            'temperature': [],
            'humidity': [],
            'description': [],
            'city': [],
            'last_updated': None
        }
    finally:
        session.close()

@app.route('/api/local/24h')
def local_24h_history():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        data = db_ops.get_local_metrics_24h()
        print("24h data:", data)  # Debug print
        return data
    finally:
        session.close()

@app.route('/api/weather/24h')
def weather_24h_history():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        return db_ops.get_weather_metrics_24h()
    finally:
        session.close()

# @app.route('/view_data')
# def view_data():
#     session = Session()
#     try:
#         local = session.query(LocalMetrics).all()
#         weather = session.query(WeatherMetrics).all()
#         return {
#             'local_metrics': [
#                 {
#                     'timestamp': m.timestamp.isoformat(),
#                     'battery': m.battery_percent,
#                     'memory': m.memory_usage
#                 } for m in local
#             ],
#             'weather_metrics': [
#                 {
#                     'timestamp': m.timestamp.isoformat(),
#                     'temperature': m.temperature,
#                     'humidity': m.humidity,
#                     'description': m.description,
#                     'city': m.city
#                 } for m in weather
#             ]
#         }
#     finally:
#         session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)