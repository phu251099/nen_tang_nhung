from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import SessionLocal, engine, Base
from datetime import datetime

class Firmware(Base):
    __tablename__ = "firmwares"
    id = Column(Integer, primary_key=True)
    version = Column(String, index=True)
    filename = Column(String, unique=True, index=True)
    size = Column(Integer)
    sha256 = Column(String, index=True)
    signature_b64 = Column(String)
    uploader = Column(String, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    jobs = relationship("Job", back_populates="firmware", cascade="all,delete")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    job_id = Column(String, unique=True, index=True)
    device_id = Column(String, index=True)
    firmware_id = Column(Integer, ForeignKey("firmwares.id"))
    state = Column(String, default="published")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    firmware = relationship("Firmware", back_populates="jobs")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    topic = Column(String)
    device_id = Column(String, index=True)
    job_id = Column(String, index=True, nullable=True)
    status = Column(String, index=True)
    payload = Column(Text)