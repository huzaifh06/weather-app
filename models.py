#Database Models for myweatherapp

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL
from datetime import datetime

Base = declarative_base()

# Weather Data Model with strict data validation
class WeatherData(Base):
    __tablename__ = 'weather_data'
    id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    temperature = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)

# Tracked City Model with city name validation
class TrackedCity(Base):
    __tablename__ = 'tracked_cities'
    id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False, unique=True)
    
    __table_args__ = (
        CheckConstraint('LENGTH(city) > 0', name='city_length_check'),
    )

#Create an engine and a session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)