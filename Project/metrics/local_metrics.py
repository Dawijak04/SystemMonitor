import psutil
import json
from datetime import datetime
from pathlib import Path

class LocalMetrics:
    """Class to handle local system metrics collection"""
    
    def __init__(self, logger):
        self.logger = logger
        self.metrics_file = Path("metrics_data.json")

    def get_metrics(self):
        """Collect local system metrics and save to JSON"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            metrics_data = {
                "metrics": {
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent
                },
                "last_updated": datetime.now().isoformat()
            }
            
            # Save metrics to JSON file
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f)
            
            return metrics_data
        except Exception as e:
            self.logger.error(f"Error getting local metrics: {str(e)}")
            return None

    def read_metrics(self):
        """Read metrics from JSON file"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            self.logger.error(f"Error reading metrics file: {str(e)}")
            return None 