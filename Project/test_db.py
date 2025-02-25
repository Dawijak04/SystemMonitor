from models import init_db
from database_manager import DatabaseOperations
from sqlalchemy.orm import sessionmaker

test_data = {
    "device_id": "dddc3487-c547-50aa-b2ce-f68c0caa1c01",
    "metrics": [
        {
            "metric_type": "battery_percent",
            "value": 62,
            "timestamp": "2025-02-25T18:27:55.207467",
            "data_type": "float",
            "unit": "%"
        },
        {
            "metric_type": "memory_usage",
            "value": 48.0,
            "timestamp": "2025-02-25T18:27:55.207467",
            "data_type": "float",
            "unit": "%"
        },
        {
            "metric_type": "temperature",
            "value": 8.6,
            "timestamp": "2025-02-25T18:27:55.299842",
            "data_type": "float",
            "unit": "°C"
        },
        {
            "metric_type": "humidity",
            "value": 71,
            "timestamp": "2025-02-25T18:27:55.299842",
            "data_type": "float",
            "unit": "%"
        },
        {
            "metric_type": "weather_description",
            "value": "broken clouds",
            "timestamp": "2025-02-25T18:27:55.299842",
            "data_type": "string",
            "unit": None
        },
        {
            "metric_type": "city",
            "value": "London",
            "timestamp": "2025-02-25T18:27:55.299842",
            "data_type": "string",
            "unit": None
        },
        {
            "metric_type": "feels_like",
            "value": 8.2,
            "timestamp": "2025-02-25T18:27:55.299842",
            "data_type": "float",
            "unit": "°C"
        }
    ]
}

if __name__ == "__main__":
    # Initialize database connection
    engine = init_db()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create database operations instance
        db_ops = DatabaseOperations(session)
        
        # Store the metrics
        success, message = db_ops.store_metrics(test_data)
        
        if success:
            print("Successfully stored metrics!")
            print(message)
        else:
            print("Failed to store metrics:")
            print(message)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()