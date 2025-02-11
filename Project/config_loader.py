import json
import os

def load_config():
    # Directly use the Project directory path
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    print(f"Looking for config file at: {config_path}")  # Debug print
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found, creating at: {config_path}")  # Debug print
        # Create a default config if it doesn't exist
        default_config = {
            "welcome_message": "Hello World",
            "logging": {
                "console_level": "INFO",
                "file_level": "WARNING",
                "log_file": "app.log",
                "format": "%(asctime)s - %(levelname)s - %(message)s"
            },
            "DEBUG": True,
            "HOST": "0.0.0.0",
            "PORT": 5000,
            "WELCOME_MESSAGE": "Hello World",
            "SECRET_KEY": "your-secret-key-here",
            "WEATHER_API_KEY": "0db44c1ef277fc786c843762e5d066ba",
            "CITY": "London"
        }
        
        # Create the config file with default values
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
            
        return default_config
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in config file")