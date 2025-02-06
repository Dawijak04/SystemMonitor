import json

    
def load_config(config_path: str = "Project/config.json"):
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at {config_path}")
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