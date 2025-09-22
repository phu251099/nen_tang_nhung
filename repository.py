from sqlalchemy.orm import Session
from models import Firmware, Job, Event

def add_firmware(db: Session, firmware: Firmware):
    db.add(firmware)
    db.commit()
    db.refresh(firmware)
    return firmware

def get_firmware_by_id(db: Session, firmware_id: int):
    return db.query(Firmware).filter(Firmware.id == firmware_id).first()

def get_firmware_by_version(db: Session, version: str):
    return db.query(Firmware).filter(Firmware.version == version).first()

def list_firmwares(db: Session):
    return db.query(Firmware).order_by(Firmware.created_at.desc()).all()

def add_job(db: Session, job: Job):
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_job_by_job_id(db: Session, job_id: str):
    return db.query(Job).filter(Job.job_id == job_id).first()

def list_jobs(db: Session):
    return db.query(Job).order_by(Job.created_at.desc()).all()

def add_event(db: Session, event: Event):
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def list_events(db: Session, limit: int = 50):
    return db.query(Event).order_by(Event.ts.desc()).limit(limit).all()