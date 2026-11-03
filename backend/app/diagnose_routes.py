from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db
from .diagnose import run_agent
from .predictor import ModelsMissing, NoPacketWindow, TelemetryNotFound

router = APIRouter()


@router.post("/diagnose/{telemetry_id}", response_model=schemas.DiagnosisOut)
def diagnose_one(telemetry_id: int, db: Session = Depends(get_db)):
    try:
        result = run_agent(db, telemetry_id)
    except TelemetryNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoPacketWindow as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ModelsMissing as e:
        raise HTTPException(status_code=503, detail=str(e))

    db.add(models.Diagnosis(
        telemetry_id=telemetry_id,
        fault_label=result["fault_label"],
        severity=result["severity"],
        confidence=result["confidence"],
        is_anomaly=result["is_anomaly"],
        verified=result["verified"],
        explanation=result["explanation"],
        sources=", ".join(result["sources"]),
    ))
    db.commit()
    return result


@router.get("/diagnoses", response_model=list[schemas.StoredDiagnosisOut])
def list_diagnoses(limit: int = Query(20, ge=1, le=500), db: Session = Depends(get_db)):
    return (
        db.query(models.Diagnosis)
        .order_by(desc(models.Diagnosis.created_at))
        .limit(limit)
        .all()
    )
