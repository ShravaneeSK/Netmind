from fastapi import Depends, FastAPI, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .merge import merged_records

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NetMind")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/telemetry", response_model=schemas.TelemetryOut, status_code=201)
def create_telemetry(reading: schemas.TelemetryIn, db: Session = Depends(get_db)):
    row = models.Telemetry(**reading.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/telemetry", response_model=list[schemas.TelemetryOut])
def list_telemetry(
    limit: int = Query(20, ge=1, le=500), db: Session = Depends(get_db)
):
    return (
        db.query(models.Telemetry)
        .order_by(desc(models.Telemetry.received_at))
        .limit(limit)
        .all()
    )


@app.post(
    "/packet-features", response_model=schemas.PacketFeaturesOut, status_code=201
)
def create_packet_features(
    features: schemas.PacketFeaturesIn, db: Session = Depends(get_db)
):
    row = models.PacketFeatures(**features.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.get("/packet-features", response_model=list[schemas.PacketFeaturesOut])
def list_packet_features(
    limit: int = Query(20, ge=1, le=500), db: Session = Depends(get_db)
):
    return (
        db.query(models.PacketFeatures)
        .order_by(desc(models.PacketFeatures.received_at))
        .limit(limit)
        .all()
    )
    


@app.get("/merged", response_model=list[schemas.MergedOut])
def list_merged(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    return merged_records(db, limit)