import os
from models import init_db, Device, MetricType, Metric
from sqlalchemy.orm import Session, sessionmaker

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'metrics.db')
    
    #removes existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")
    
    #creates new database and gets engine
    engine = init_db()
    print(f"Created new database at {db_path}")
