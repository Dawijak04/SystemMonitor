from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import os

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(String(100), unique=True, nullable=False) 
    last_seen = Column(DateTime, default=datetime.utcnow)
    admin = Column(Boolean, default=False)

    metrics = relationship("Metric", back_populates="device", cascade="all, delete-orphan")

class MetricType(Base):
    __tablename__ = 'metric_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True) 
    data_type = Column(String(20))
    unit = Column(String(20)) 

    metrics = relationship("Metric", back_populates="metric_type", cascade="all, delete-orphan")

class Metric(Base):
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    value = Column(String(255), nullable=False)
    
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    metric_type_id = Column(Integer, ForeignKey('metric_types.id'), nullable=False)
    
    device = relationship("Device", back_populates="metrics")
    metric_type = relationship("MetricType", back_populates="metrics")

def init_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'metrics.db')
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine 