from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .predictor import ModelsMissing, NoPacketWindow, build_record, predict

router = APIRouter()


def _plain(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


@router.get("/latest")
def latest(db: Session = Depends(get_db)):
    """Newest telemetry reading with its packet window and a prediction (not stored)."""
    row = db.query(models.Telemetry).order_by(desc(models.Telemetry.received_at)).first()
    if row is None:
        raise HTTPException(status_code=404, detail="No telemetry yet")

    prediction, note = None, None
    try:
        record = build_record(db, row.id)
        prediction = predict(record)
    except NoPacketWindow:
        record = _plain(row)
        note = "No packet features near this reading, so no prediction was made."
    except ModelsMissing as e:
        record = _plain(row)
        note = str(e)
    return {"record": record, "prediction": prediction, "note": note}
