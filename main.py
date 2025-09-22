import os
import json
import base64
import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Query, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import paho.mqtt.client as mqtt

from database import SessionLocal, engine, Base
from models import Base, Firmware, Job, Event
from schemas import FirmwareOut, JobCreate, JobOut, EventOut
from services import (
    STORAGE_DIR, sha256_of_bytes, sign_bytes_ed25519, VERIFY_KEY, build_full_url
)
from repository import (
    add_firmware, get_firmware_by_id, get_firmware_by_version, list_firmwares,
    add_job, get_job_by_job_id, list_jobs, add_event, list_events
)
from typing import List

# MQTT config
mqtt_broker_address = "10.14.80.150"
mqtt_port = 8883
mqtt_user = "iot"
mqtt_password = "1"

# mqtt_broker_address = "10.14.81.131"
# mqtt_port = 1883
# mqtt_user = "mqtt"
# mqtt_password = "thaco"

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")

# MQTT setup
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected rc={rc}")
    client.subscribe("ota/status/#", qos=1)

def on_message(client, userdata, msg):
    print("sub")    
    try:
        payload = msg.payload.decode(errors="replace")
        data = json.loads(payload)
        device_id = data.get("device_id") or infer_device_from_topic(msg.topic)
        status = data.get("status", "unknown")
        job_id = data.get("job_id")
        with SessionLocal() as db:
            ev = Event(topic=msg.topic, device_id=device_id, job_id=job_id, status=status, payload=payload)
            add_event(db, ev)
            if job_id and status in {"downloading", "installing", "completed", "failed"}:
                db_job = get_job_by_job_id(db, job_id)
                if db_job:
                    db_job.state = status
            db.commit()
    except Exception as e:
        print(f"[MQTT] on_message error: {e}")

def infer_device_from_topic(topic: str):
    parts = topic.split("/")
    if len(parts) >= 3:
        return parts[2]
    return None

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(mqtt_user, password=mqtt_password)
client.connect(mqtt_broker_address, port=mqtt_port)
client.loop_start()
# client.loop_forever()

# FastAPI app
app = FastAPI(title="OTA Management Server")
app.mount("/static/firmwares", StaticFiles(directory=STORAGE_DIR), name="firmwares")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/public_key")
def get_public_key_hex():
    import binascii
    return {"ed25519_public_key_hex": binascii.hexlify(VERIFY_KEY.encode()).decode()}

@app.post("/upload", response_model=FirmwareOut)
async def upload_firmware(
    request: Request,
    file: UploadFile = File(...),
    version: str = Form(None),
    uploader: str = Form("admin"),
    db: Session = Depends(get_db)
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    digest = sha256_of_bytes(data)
    signature_b64 = sign_bytes_ed25519(data)
    safe_name = file.filename
    fw_path = STORAGE_DIR / safe_name
    sig_path = STORAGE_DIR / f"{safe_name}.sig"
    fw_path.write_bytes(data)
    sig_path.write_bytes(base64.b64decode(signature_b64))
    row = Firmware(
        version=version or safe_name,
        filename=safe_name,
        size=len(data),
        sha256=digest,
        signature_b64=signature_b64,
        uploader=uploader,
    )
    add_firmware(db, row)
    return row

@app.get("/firmwares", response_model=List[FirmwareOut])
def list_firmwares_api(db: Session = Depends(get_db)):
    return list_firmwares(db)

@app.get("/firmwares/by_version/{version_id}", response_model=FirmwareOut)
def list_firmwares_by_version_api(version_id = str, db: Session = Depends(get_db)):
    return get_firmware_by_version(db, version_id)

@app.get("/firmwares/by_frimware/{firmware_id}", response_model=FirmwareOut)
def list_firmwares_by_id_api(firmware_id = int, db: Session = Depends(get_db)):
    return get_firmware_by_id(db, firmware_id)


@app.post("/jobs", response_model=JobOut)
async def create_job(body: JobCreate, request: Request, db: Session = Depends(get_db)):
    if body.firmware_id is not None:
        fw = get_firmware_by_id(db, body.firmware_id)
    elif body.firmware_version:
        fw = get_firmware_by_version(db, body.firmware_version)
    else:
        raise HTTPException(status_code=400, detail="Provide firmware_id or firmware_version")
    if not fw:
        raise HTTPException(status_code=404, detail="Firmware not found")
    job_id = f"J-{int(time.time())}"
    job = Job(job_id=job_id, device_id=body.device_id, firmware_id=fw.id, state="published")
    add_job(db, job)
    download_rel = f"/static/firmwares/{fw.filename}"
    sig_rel = f"/static/firmwares/{fw.filename}.sig"
    download_url = build_full_url(request, download_rel, PUBLIC_BASE_URL)
    signature_url = build_full_url(request, sig_rel, PUBLIC_BASE_URL)
    cmd = {
        "job_id": job_id,
        "type": "firmware",
        "version": fw.version,
        "download_url": download_url,
        "signature_url": signature_url,
        "size": fw.size,
        "sha256": fw.sha256,
        "algo": "sha256+ed25519",
        "strategy": "AB",
        "retry": {"max": 3, "backoff_sec": 60},
    }
    topic = f"ota/cmd/{body.device_id}"
    client.publish(topic, json.dumps(cmd), qos=1, retain=False)
    return JobOut(job_id=job_id, device_id=body.device_id, firmware_version=fw.version, state="published")

@app.get("/jobs")
def list_jobs_api(db: Session = Depends(get_db)):
    jobs = list_jobs(db)
    out = []
    for j in jobs:
        out.append({
            "job_id": j.job_id,
            "device_id": j.device_id,
            "firmware_version": j.firmware.version if j.firmware else None,
            "state": j.state,
            "created_at": j.created_at.isoformat(),
        })
    return out

@app.get("/events")
def list_events_api(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    events = list_events(db, limit)
    return [
        EventOut(
            ts=r.ts,
            device_id=r.device_id,
            topic=r.topic,
            status=r.status,
            job_id=r.job_id,
            payload=r.payload,
        )
        for r in events
    ]