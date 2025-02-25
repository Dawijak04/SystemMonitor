import os
from models import init_db, Device, MetricType, Metric
from sqlalchemy.orm import Session, sessionmaker

if __name__ == "__main__":
    # Get the database path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'metrics.db')
    
    # Delete existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")
    
    # Create new database and get engine
    engine = init_db()
    print(f"Created new database at {db_path}")

    # Create session factory bound to the engine
    SessionMaker = sessionmaker(bind=engine)

    # Create an admin device (optional)
    with SessionMaker() as session:
        admin_device = Device(
            device_id="dddc3487-c547-50aa-b2ce-f68c0caa1c01",
            admin=True
        )
        session.add(admin_device)
        session.commit()
        print("Created admin device")

    print("Database initialization complete!")