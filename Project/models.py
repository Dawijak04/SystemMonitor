from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import os

Base = declarative_base()

class LocalMetrics(Base):
    __tablename__ = 'local_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    battery_percent = Column(Float, nullable=True)
    memory_usage = Column(Float)

class WeatherMetrics(Base):
    __tablename__ = 'weather_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    description = Column(String(100))
    city = Column(String(100))

# Create database and tables
def init_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'metrics.db')
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine  # Return the engine 