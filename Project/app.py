from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import secrets  # for generating secure random string

app = Flask(__name__)
# Generate a secure random key
app.config['SECRET_KEY'] = secrets.token_hex(16)  # generates a 32-character hex string
# Add CORS settings for Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Store latest metrics
latest_metrics = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/local')
def local():
    return render_template('local.html')

@app.route('/weather')
def weather():
    return render_template('weather.html')

@socketio.on('connect')
def handle_connect():
    print("Client connected")  # Debug log
    # Send latest metrics immediately if we have them
    if latest_metrics:
        emit('metrics_update', latest_metrics)

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")  # Debug log

@socketio.on('metrics_update')
def handle_metrics(data):
    global latest_metrics
    latest_metrics = data  # Store the latest metrics
    print(f"Received metrics: {data}")  # Debug log
    # Broadcast received metrics to all clients
    emit('metrics_update', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 