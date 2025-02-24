from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import LocalMetrics, WeatherMetrics, init_db
import json
import secrets
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Initialize database and create session maker
engine = init_db()
Session = sessionmaker(bind=engine)

def get_latest_metrics():
    session = Session()
    try:
        latest_local = session.query(LocalMetrics).order_by(LocalMetrics.timestamp.desc()).first()
        latest_weather = session.query(WeatherMetrics).order_by(WeatherMetrics.timestamp.desc()).first()

        print("Debug - Latest Local:", latest_local)  # Debug log
        print("Debug - Latest Weather:", latest_weather)  # Debug log

        metrics = {}
        if latest_local:
            metrics['local'] = {
                'battery_percent': latest_local.battery_percent,
                'memory_usage': latest_local.memory_usage
            }
        if latest_weather:
            metrics['weather'] = {
                'temperature': latest_weather.temperature,
                'humidity': latest_weather.humidity,
                'description': latest_weather.description,
                'city': latest_weather.city
            }
        print("Debug - Returning metrics:", metrics)  # Debug log
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
        latest = session.query(LocalMetrics).order_by(LocalMetrics.timestamp.desc()).first()
        initial_data = {
            'local': {
                'battery_percent': latest.battery_percent,
                'memory_usage': latest.memory_usage,
                'timestamp': latest.timestamp.isoformat()
            }
        } if latest else None
        print("Loading local page, latest metrics:", initial_data)  # Debug log
        return render_template('local.html', initial_data=initial_data)
    finally:
        session.close()

@app.route('/weather')
def weather():
    session = Session()
    try:
        latest = session.query(WeatherMetrics).order_by(WeatherMetrics.timestamp.desc()).first()
        initial_data = {
            'weather': {
                'temperature': latest.temperature,
                'humidity': latest.humidity,
                'description': latest.description,
                'city': latest.city,
                'timestamp': latest.timestamp.isoformat()
            }
        } if latest else None
        return render_template('weather.html', initial_data=initial_data)
    finally:
        session.close()

@app.route('/metrics', methods=['POST'])
def handle_metrics():
    metrics = request.json
    print("Received metrics update:", metrics)
    session = Session()

    try:
        if 'local' in metrics:
            local = LocalMetrics(
                battery_percent=metrics['local']['battery_percent'],
                memory_usage=metrics['local']['memory_usage']
            )
            session.add(local)

        if 'weather' in metrics:
            weather = WeatherMetrics(
                temperature=metrics['weather']['temperature'],
                humidity=metrics['weather']['humidity'],
                description=metrics['weather']['description'],
                city=metrics['weather']['city']
            )
            session.add(weather)

        session.commit()
        print("Metrics saved to database")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error saving metrics: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/api/history/local')
def local_history():
    session = Session()
    try:
        latest = session.query(LocalMetrics).order_by(LocalMetrics.timestamp.desc()).first()
        if latest:
            return {
                'timestamps': [latest.timestamp.isoformat()],
                'battery': [latest.battery_percent],
                'memory': [latest.memory_usage],
                'last_updated': latest.timestamp.isoformat()
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
        latest = session.query(WeatherMetrics).order_by(WeatherMetrics.timestamp.desc()).first()
        if latest:
            return {
                'timestamps': [latest.timestamp.isoformat()],
                'temperature': [latest.temperature],
                'humidity': [latest.humidity],
                'description': [latest.description],
                'city': [latest.city],
                'last_updated': latest.timestamp.isoformat()
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

@app.route('/view_data')
def view_data():
    session = Session()
    try:
        local = session.query(LocalMetrics).all()
        weather = session.query(WeatherMetrics).all()
        return {
            'local_metrics': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'battery': m.battery_percent,
                    'memory': m.memory_usage
                } for m in local
            ],
            'weather_metrics': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'temperature': m.temperature,
                    'humidity': m.humidity,
                    'description': m.description,
                    'city': m.city
                } for m in weather
            ]
        }
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)