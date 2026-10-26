from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db
from .predictor import (ModelsMissing, NoPacketWindow, TelemetryNotFound,
                        build_record, predict)

router = APIRouter()


@router.post("/predict/{telemetry_id}", response_model=schemas.PredictionOut)
def predict_one(telemetry_id: int, db: Session = Depends(get_db)):
    try:
        record = build_record(db, telemetry_id)
        result = predict(record)
    except TelemetryNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoPacketWindow as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ModelsMissing as e:
        raise HTTPException(status_code=503, detail=str(e))

    db.add(models.Prediction(
        telemetry_id=telemetry_id,
        anomaly_score=result["anomaly_score"],
        fault_label=result["fault_label"],
        severity=result["severity"],
    ))
    db.commit()
    return {"telemetry_id": telemetry_id, **result}


@router.get("/predictions", response_model=list[schemas.StoredPredictionOut])
def list_predictions(limit: int = Query(20, ge=1, le=500), db: Session = Depends(get_db)):
    return (
        db.query(models.Prediction)
        .order_by(desc(models.Prediction.created_at))
        .limit(limit)
        .all()
    )
