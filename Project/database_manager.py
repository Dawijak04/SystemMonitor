from sqlalchemy.orm import Session
from models import Device, MetricType, Metric
from datetime import datetime, timedelta
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
            device = self.session.query(Device).filter_by(device_id=metrics_data["device_id"]).first()
            if not device:
                device = Device(device_id=metrics_data["device_id"])
                self.session.add(device)
                self.session.flush()
            
            device.last_seen = datetime.utcnow()
            if metrics_data["device_id"] != self.config["admin_device_id"]:
                return True, "Device registered, but doesn't have admin rights"
            
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
                
                # Create new metric
                new_metric = Metric(
                    timestamp=datetime.fromisoformat(metric["timestamp"]),
                    value=str(metric["value"]),
                    device_id=device.id,
                    metric_type_id=metric_type.id
                )
                self.session.add(new_metric)
            
            self.session.commit()
            return True, "Metrics stored successfully"
        except Exception as e:
            self.session.rollback()
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
