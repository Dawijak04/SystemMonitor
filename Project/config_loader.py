import json
import os

def load_config():
    # Get the absolute path to the project directory
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_dir, 'Project', 'config.json')
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create a default config if it doesn't exist
        default_config = {
            "WEATHER_API_KEY": "",  # You'll need to set this in PythonAnywhere
            "LOG_LEVEL": "INFO",
            "LOG_FILE": "app.log"
        }
        
        # Create the config file with default values
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
            
        return default_config
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in config file")

# def get(self, *keys, default=None):
#     value = self.config
#     for key in keys:
#         try:
#             value = value[key]
#         except (KeyError, TypeError):
#             return default
#     return value