from sqlalchemy.orm import Session
from models import Device, MetricType, Metric
from datetime import datetime, timedelta, timezone
import json
import os

class DatabaseOperations:
    def __init__(self, session: Session):
        self.session = session
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)

    def store_metrics(self, metrics_data: dict):
        """Store metrics from a device"""
        try:
            # Log the incoming device ID for debugging
            print(f"Processing metrics from device ID: {metrics_data['device_id']}")
            
            device = self.session.query(Device).filter_by(device_id=metrics_data["device_id"]).first()
            is_new_device = False
            
            if not device:
                is_new_device = True
                device = Device(device_id=metrics_data["device_id"], admin=False)
                self.session.add(device)
                self.session.flush()
                print(f"Created new device with ID: {device.device_id}, admin status: {device.admin}")
            else:
                print(f"Found existing device with ID: {device.device_id}, admin status: {device.admin}")
            
            device.last_seen = datetime.utcnow()
            
            # Check for admin passkey and grant admin rights if valid
            if "passkey" in metrics_data and metrics_data["passkey"] == self.config.get("admin_passkey"):
                print(f"Valid admin passkey provided for device: {device.device_id}")
                device.admin = True
                self.session.flush()
                print(f"Updated admin status to: {device.admin}")
            
            # Make sure we commit the device changes before checking admin status
            self.session.commit()
            
            # Re-query to ensure we have the latest data
            device = self.session.query(Device).filter_by(device_id=metrics_data["device_id"]).first()
            
            if not device.admin:
                print(f"Device {device.device_id} doesn't have admin rights")
                return True, "Device registered, but doesn't have admin rights"
            
            print(f"Processing metrics for admin device: {device.device_id}")
            
            for metric in metrics_data["metrics"]:
                metric_type = self.session.query(MetricType).filter_by(name=metric["metric_type"]).first()
                if not metric_type:
                    metric_type = MetricType(
                        name=metric["metric_type"],
                        data_type=metric["data_type"],
                        unit=metric["unit"]
                    )
                    self.session.add(metric_type)
                    self.session.flush()
                
                # Parse the timestamp and ensure it's in UTC
                timestamp = datetime.fromisoformat(metric["timestamp"])
                # If the timestamp doesn't have timezone info, assume it's in UTC
                if timestamp.tzinfo is None:
                    # Create a UTC timestamp
                    timestamp = timestamp.replace(tzinfo=None)  # Ensure no timezone info for SQLite compatibility
                else:
                    # Convert to UTC and remove timezone info for storage
                    timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
                
                # Create new metric with UTC timestamp
                new_metric = Metric(
                    timestamp=timestamp,
                    value=str(metric["value"]),
                    device_id=device.id,
                    metric_type_id=metric_type.id
                )
                self.session.add(new_metric)
            
            self.session.commit()
            return True, "Metrics stored successfully"
        except Exception as e:
            self.session.rollback()
            print(f"Error in store_metrics: {str(e)}")
            return False, str(e)
        

    def get_latest_weather_metrics(self):
        """Get latest weather-related metrics"""
        try:
            weather_types = ["temperature", "humidity", "weather_description", "city"]
            latest_metrics = {}
            
            for metric_type_name in weather_types:
                metric = (self.session.query(Metric, MetricType)
                    .join(MetricType)
                    .filter(MetricType.name == metric_type_name)
                    .order_by(Metric.timestamp.desc())
                    .first())
                
                if metric:
                    metric_value, _ = metric
                    latest_metrics[metric_type_name] = metric_value.value

                    if 'timestamp' not in latest_metrics:
                        latest_metrics['timestamp'] = metric_value.timestamp.isoformat()

            if latest_metrics:
                return {
                    'weather': {
                        'temperature': latest_metrics.get('temperature'),
                        'humidity': latest_metrics.get('humidity'),
                        'description': latest_metrics.get('weather_description'),
                        'city': latest_metrics.get('city'),
                        'timestamp': latest_metrics.get('timestamp')
                    }
                }
            return None
            
        except Exception as e:
            self.session.rollback()
            return {'error': str(e)}
        

    def get_latest_local_metrics(self):
        """Get latest local system metrics"""
        try:
            local_types = ["battery_percent", "memory_usage"]
            latest_metrics = {}
            
            for metric_type_name in local_types:
                metric = (self.session.query(Metric, MetricType)
                    .join(MetricType)
                    .filter(MetricType.name == metric_type_name)
                    .order_by(Metric.timestamp.desc())
                    .first())
                
                if metric:
                    metric_value, _ = metric
                    latest_metrics[metric_type_name] = metric_value.value
                    
                    if 'timestamp' not in latest_metrics:
                        latest_metrics['timestamp'] = metric_value.timestamp.isoformat()

            if latest_metrics:
                return {
                    'local': {
                        'battery_percent': latest_metrics.get('battery_percent'),
                        'memory_usage': latest_metrics.get('memory_usage'),
                        'timestamp': latest_metrics.get('timestamp')
                    }
                }
            return None
            
        except Exception as e:
            self.session.rollback()
            return {'error': str(e)}


    def get_local_metrics_24h(self):
        """Get local metrics for the last 24 hours"""
        try:
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            metrics = {}
            timestamps = set()
            
            for metric_type_name in ["battery_percent", "memory_usage"]:
                results = (self.session.query(Metric, MetricType)
                    .join(MetricType)
                    .filter(
                        MetricType.name == metric_type_name,
                        Metric.timestamp >= twenty_four_hours_ago
                    )
                    .order_by(Metric.timestamp.asc())  
                    .all())
                
                if results:
                    key = "battery" if metric_type_name == "battery_percent" else "memory"
                    metrics[key] = [float(m[0].value) for m in results]
                    timestamps.update(m[0].timestamp.isoformat() for m in results)
            
            # Convert timestamps to sorted list
            timestamps_list = sorted(list(timestamps))
            
            if metrics:
                return {
                    'timestamps': timestamps_list,
                    'battery': metrics.get('battery', []),
                    'memory': metrics.get('memory', []),
                }
            
            return {
                'timestamps': [],
                'battery': [],
                'memory': []
            }
            
        except Exception as e:
            self.session.rollback()
            return {'error': str(e)}

    def get_weather_metrics_24h(self):
        """Get weather metrics for the last 24 hours"""
        try:
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            metrics = {}
            timestamps = set()
            
            for metric_type_name in ["temperature", "humidity"]:
                results = (self.session.query(Metric, MetricType)
                    .join(MetricType)
                    .filter(
                        MetricType.name == metric_type_name,
                        Metric.timestamp >= twenty_four_hours_ago
                    )
                    .order_by(Metric.timestamp.asc())
                    .all())
                
                if results:
                    metrics[metric_type_name] = [float(m[0].value) for m in results]
                    timestamps.update(m[0].timestamp.isoformat() for m in results)
            
            # Convert timestamps to sorted list
            timestamps_list = sorted(list(timestamps))
            
            if metrics:
                return {
                    'timestamps': timestamps_list,
                    'temperature': metrics.get('temperature', []),
                    'humidity': metrics.get('humidity', [])
                }
            
            return {
                'timestamps': [],
                'temperature': [],
                'humidity': []
            }
            
        except Exception as e:
            self.session.rollback()
            return {'error': str(e)}
