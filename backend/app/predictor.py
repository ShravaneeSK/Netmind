"""Run the saved NetMind models on one reading.

Loads the Random Forest fault classifier and the Isolation Forest anomaly detector
from ml/models (prefix set by MODEL_PREFIX in .env, default "sim"), builds the merged
record for a telemetry row (nearest packet window within 5 s) and returns a prediction.

Models trained on simulated data only check that this code works.
"""
import os
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from . import models
from .merge import PACKET_FIELDS, WINDOW
from .severity import severity

MODELS_DIR = Path(__file__).resolve().parents[2] / "ml" / "models"


class ModelsMissing(RuntimeError):
    pass


class TelemetryNotFound(LookupError):
    pass


class NoPacketWindow(LookupError):
    pass


@lru_cache(maxsize=1)
def load_models():
    prefix = os.getenv("MODEL_PREFIX", "sim")
    files = {
        "fault": MODELS_DIR / f"{prefix}_fault_rf.joblib",
        "anomaly": MODELS_DIR / f"{prefix}_anomaly_if.joblib",
    }
    missing = [p.name for p in files.values() if not p.exists()]
    if missing:
        raise ModelsMissing(
            "Missing model files in ml/models: " + ", ".join(missing)
            + ". Run python ml/train.py first."
        )
    return {name: joblib.load(path) for name, path in files.items()}


def build_record(db: Session, telemetry_id: int) -> dict:
    """One telemetry row plus its nearest packet window (within 5 s)."""
    row = db.get(models.Telemetry, telemetry_id)
    if row is None:
        raise TelemetryNotFound(f"No telemetry row with id {telemetry_id}")
    record = {c.name: getattr(row, c.name) for c in row.__table__.columns}

    candidates = (
        db.query(models.PacketFeatures)
        .filter(
            models.PacketFeatures.received_at >= row.received_at - WINDOW,
            models.PacketFeatures.received_at <= row.received_at + WINDOW,
        )
        .all()
    )
    if not candidates:
        raise NoPacketWindow(
            f"No packet features within 5 s of telemetry {telemetry_id}. Is the collector running?"
        )
    nearest = min(
        candidates, key=lambda p: abs((p.received_at - row.received_at).total_seconds())
    )
    for name in PACKET_FIELDS:
        record[name] = getattr(nearest, name)
    return record


def predict(record: dict) -> dict:
    bundle = load_models()
    fault, anomaly = bundle["fault"], bundle["anomaly"]
    frame = pd.DataFrame([record])

    proba = fault["model"].predict_proba(frame[fault["features"]])[0]
    order = proba.argsort()[::-1]
    label = str(fault["classes"][int(order[0])])
    top = {str(fault["classes"][int(i)]): round(float(proba[i]), 3) for i in order[:3]}

    score = float(anomaly["model"].decision_function(frame[anomaly["features"]])[0])
    is_anomaly = score < anomaly["threshold"]

    level, reasons = severity(label, record)
    if label == "normal" and is_anomaly:
        reasons.append(
            "the anomaly detector flagged this reading although the classifier says normal"
        )

    return {
        "fault_label": label,
        "confidence": round(float(proba[order[0]]), 3),
        "top_classes": top,
        "is_anomaly": bool(is_anomaly),
        "anomaly_score": round(score, 4),
        "severity": level,
        "reasons": reasons,
    }
