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

            print(f"Processing metrics from device ID: {metrics_data['device_id']}")
            
            device = self.session.query(Device).filter_by(device_id=metrics_data["device_id"]).first()
            
            #if device is new, register to it db 
            if not device:
                device = Device(device_id=metrics_data["device_id"], admin=False)
                self.session.add(device)
                self.session.flush()
                print(f"Created new device with ID: {device.device_id}, admin status: {device.admin}")
            else:
                print(f"Found existing device with ID: {device.device_id}, admin status: {device.admin}")
            
            device.last_seen = datetime.now(timezone.utc)
            
            #check for admin passkey 
            if "passkey" in metrics_data and metrics_data["passkey"] == self.config.get("admin_passkey") and device.admin == False:
                print(f"Valid admin passkey provided for device: {device.device_id}")
                device.admin = True
                self.session.flush()
                print(f"Updated admin status to: {device.admin}")
            
            self.session.commit()
            
            #re-query to ensure latest data
            device = self.session.query(Device).filter_by(device_id=metrics_data["device_id"]).first()
            
            if not device.admin:
                print(f"Device {device.device_id} doesn't have admin rights")
                return True, "Device registered, but doesn't have admin rights"
            
            print(f"Processing metrics for device: {device.device_id}")
            
            #check if metrics type exists in db, if not, registers it 
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
                
                #parse timestamp and ensure it's in UTC
                timestamp = datetime.fromisoformat(metric["timestamp"])

                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=None)  #no tz info for SQLite compatibility
                else:
                    timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)


                #create new metric 
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
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            
            metrics_by_timestamp = {}
            
            for metric_type_name in ["battery_percent", "memory_usage"]:
                results = (self.session.query(Metric, MetricType)
                    .join(MetricType)
                    .filter(
                        MetricType.name == metric_type_name,
                        Metric.timestamp >= twenty_four_hours_ago
                    )
                    .order_by(Metric.timestamp.asc())  
                    .all())
                
                for m in results:
                    timestamp = m[0].timestamp.isoformat() + "+00:00"
                    value = float(m[0].value)
                    
                    if timestamp not in metrics_by_timestamp:
                        metrics_by_timestamp[timestamp] = {}
                    
                    key = "battery" if metric_type_name == "battery_percent" else "memory"
                    metrics_by_timestamp[timestamp][key] = value
            
            sorted_timestamps = sorted(metrics_by_timestamp.keys())
            
            battery_values = []
            memory_values = []
            
            last_battery = 0
            last_memory = 0
            
            for ts in sorted_timestamps:
                metrics = metrics_by_timestamp[ts]

                if "battery" in metrics:
                    last_battery = metrics["battery"]
                battery_values.append(last_battery)
                
                if "memory" in metrics:
                    last_memory = metrics["memory"]
                memory_values.append(last_memory)
            
            
            return {
                'timestamps': sorted_timestamps,
                'battery': battery_values,
                'memory': memory_values,
            }
            
        except Exception as e:
            self.session.rollback()
            print(f"Error in get_local_metrics_24h: {str(e)}")
            return {'error': str(e)}

    def get_weather_metrics_24h(self):
        """Get weather metrics for the last 24 hours"""
        try:
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            
            metrics_by_timestamp = {}
            
            for metric_type_name in ["temperature", "humidity"]:
                results = (self.session.query(Metric, MetricType)
                    .join(MetricType)
                    .filter(
                        MetricType.name == metric_type_name,
                        Metric.timestamp >= twenty_four_hours_ago
                    )
                    .order_by(Metric.timestamp.asc())  
                    .all())
                
                for m in results:
                    timestamp = m[0].timestamp.isoformat() + "+00:00"
                    value = float(m[0].value)
                    
                    if timestamp not in metrics_by_timestamp:
                        metrics_by_timestamp[timestamp] = {}
                    
                    metrics_by_timestamp[timestamp][metric_type_name] = value
            
            sorted_timestamps = sorted(metrics_by_timestamp.keys())
            
            temp_values = []
            humidity_values = []
            
            last_temp = 0
            last_humidity = 0
            
            for ts in sorted_timestamps:
                metrics = metrics_by_timestamp[ts]

                if "temperature" in metrics:
                    last_temp = metrics["temperature"]
                temp_values.append(last_temp)
                
                if "humidity" in metrics:
                    last_humidity = metrics["humidity"]
                humidity_values.append(last_humidity)
            
            
            return {
                'timestamps': sorted_timestamps,
                'temperature': temp_values,
                'humidity': humidity_values
            }
            
        except Exception as e:
            self.session.rollback()
            print(f"Error in get_weather_metrics_24h: {str(e)}")
            return {'error': str(e)}
