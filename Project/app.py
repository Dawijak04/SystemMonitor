from flask import Flask, render_template, request, jsonify
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
from models import init_db, Device
import secrets
from database_manager import DatabaseOperations

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = secrets.token_hex(16)

#creates connection to database and session 
engine = init_db()
Session = sessionmaker(bind=engine)

last_commands = {}


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
            print("Metrics handled successfully")
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
            return jsonify({
                'timestamps': [latest['local']['timestamp']],
                'battery': [float(latest['local']['battery_percent'])],
                'memory': [float(latest['local']['memory_usage'])],
                'last_updated': latest['local']['timestamp']
            })

        return jsonify({
            'timestamps': [],
            'battery': [],
            'memory': [],
            'last_updated': None
        })
    finally:
        session.close()

@app.route('/api/history/weather')
def weather_history():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        latest = db_ops.get_latest_weather_metrics()
        
        if latest and 'weather' in latest:
            return jsonify({
                'timestamps': [latest['weather']['timestamp']],
                'temperature': [float(latest['weather']['temperature'])],
                'humidity': [float(latest['weather']['humidity'])],
                'description': [latest['weather']['description']],
                'city': [latest['weather']['city']],
                'last_updated': latest['weather']['timestamp']
            })
        
        return jsonify({
            'timestamps': [],
            'temperature': [],
            'humidity': [],
            'description': [],
            'city': [],
            'last_updated': None
        })
    finally:
        session.close()


@app.route('/api/local/24h')
def local_24h_history():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        data = db_ops.get_local_metrics_24h() 
        return jsonify(data)
    finally:
        session.close()

@app.route('/api/weather/24h')
def weather_24h_history():
    session = Session()
    try:
        db_ops = DatabaseOperations(session)
        return jsonify(db_ops.get_weather_metrics_24h())
    finally:
        session.close()


@app.route('/api/command/<device_id>', methods=['POST'])
def send_command(device_id):
    """POSTS command to endpoint"""

    command = request.json.get('command')
    print(f"Received command request for device {device_id}: {command}") 

    if not command:
        return jsonify({"status": "error", "message": "No command specified"}), 400

    last_commands[device_id] = command
    return jsonify({"status": "success", "message": "Command sent successfully", "command": command}), 200


@app.route('/api/command/<device_id>', methods=['GET'])
def get_commands(device_id):
    """GETS command from endpoint"""

    command = last_commands.pop(device_id, None)
    print(f"Device {device_id} checking for commands, returning: {command}")  
    return jsonify({"command": command}), 200


@app.route('/api/default_device', methods=['GET'])
def get_default_device():
    print("Getting default device...")
    session = Session()
    try:
        device = session.query(Device).order_by(desc(Device.last_seen)).first()
        print(f"Found device: {device}") 
        
        if device:
            return jsonify({"device_id": device.device_id})
        
        print("No device found")  
        return jsonify({"device_id": None, "error": "No active device found"}), 404
    finally:
        session.close()

@app.route('/debug/devices')
def debug_devices():
    session = Session()
    try:
        devices = session.query(Device).all()
        return jsonify({
            "devices": [
                {
                    "id": d.id,
                    "device_id": d.device_id,
                    "last_seen": d.last_seen.isoformat() if d.last_seen else None
                }
                for d in devices
            ]
        })
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)