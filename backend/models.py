from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, DateTime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from backend.db_config import Base, db

class User(UserMixin, Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class AQIData(Base):
    __tablename__ = 'aqi_data'
    
    id = Column(Integer, primary_key=True)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    aqi_value = Column(Float)
    aqi_category = Column(String(50))
    pm25_value = Column(Float)
    pm25_category = Column(String(50))
    pm10_value = Column(Float)
    pm10_category = Column(String(50))
    o3_value = Column(Float)
    o3_category = Column(String(50))
    no2_value = Column(Float)
    no2_category = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    continent = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)

class CountryAQI(Base):
    __tablename__ = 'country_aqi'
    
    id = Column(Integer, primary_key=True)
    country = Column(String(100), nullable=False)
    rank = Column(Integer)
    avg_aqi = Column(Float)
    jan = Column(Float)
    feb = Column(Float)
    mar = Column(Float)
    apr = Column(Float)
    may = Column(Float)
    jun = Column(Float)
    jul = Column(Float)
    aug = Column(Float)
    sep = Column(Float)
    oct = Column(Float)
    nov = Column(Float)
    dec = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class CityAQI(Base):
    __tablename__ = 'city_aqi'
    
    id = Column(Integer, primary_key=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    country = Column(String(100))
    jan = Column(Float)
    feb = Column(Float)
    mar = Column(Float)
    apr = Column(Float)
    may = Column(Float)
    jun = Column(Float)
    jul = Column(Float)
    aug = Column(Float)
    sep = Column(Float)
    oct = Column(Float)
    nov = Column(Float)
    dec = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)