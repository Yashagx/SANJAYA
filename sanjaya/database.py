from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", 
    "postgresql://sanjaya_user:Sanjaya2026!@localhost:5432/sanjaya_db")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    vessel_id = Column(String(100))
    origin = Column(String(200))
    destination = Column(String(200))
    route = Column(String(400))
    risk_score = Column(Float)
    risk_level = Column(String(20))
    recommendation = Column(Text)
    p_delay = Column(Float)
    s_weather = Column(Float)
    s_geo = Column(Float)
    c_port = Column(Float)
    customs_risk = Column(Float)
    weather_condition = Column(String(200))
    geo_headline = Column(Text)
    days_real = Column(Integer)
    days_scheduled = Column(Integer)
    transport_mode = Column(String(50), default="sea")
    shap_top_factor = Column(String(200))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_assessment(result: dict, payload: dict):
    db = SessionLocal()
    try:
        assessment = RiskAssessment(
            vessel_id=result.get("vessel_id"),
            origin=payload.get("origin"),
            destination=payload.get("destination"),
            route=result.get("route"),
            risk_score=result.get("risk_score"),
            risk_level=result.get("risk_level"),
            recommendation=result.get("recommendation"),
            p_delay=result["breakdown"].get("p_delay"),
            s_weather=result["breakdown"].get("s_weather"),
            s_geo=result["breakdown"].get("s_geo"),
            c_port=result["breakdown"].get("c_port"),
            customs_risk=result["breakdown"].get("customs_risk"),
            weather_condition=result["evidence"]["weather"].get("condition"),
            geo_headline=result["evidence"]["geopolitics"].get("top_headline"),
            days_real=payload.get("days_real"),
            days_scheduled=payload.get("days_scheduled"),
            transport_mode=payload.get("transport_mode", "sea")
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment.id
    except Exception as e:
        db.rollback()
        print(f"DB save error: {e}")
        return None
    finally:
        db.close()
