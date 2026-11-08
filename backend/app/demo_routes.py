import os
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models
from .database import get_db

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # so the simulator package can be imported

router = APIRouter()


@router.post("/demo/{fault}")
def demo_inject(fault: str, db: Session = Depends(get_db)):
    """Insert one simulated reading and packet window for a demo. Never labelled."""
    if os.getenv("DEMO_MODE", "1") == "0":
        raise HTTPException(status_code=403, detail="Demo mode is switched off")

    from simulator.simulate import FAULTS, generate

    if fault not in FAULTS:
        raise HTTPException(
            status_code=404, detail="Unknown fault. Choose one of: " + ", ".join(FAULTS)
        )

    tel, pkt = generate(fault)
    tel["device_id"] = "demo"
    db.add(models.PacketFeatures(**pkt))
    telemetry_row = models.Telemetry(**tel)
    db.add(telemetry_row)
    db.commit()
    db.refresh(telemetry_row)
    return {"telemetry_id": telemetry_row.id, "fault_injected": fault}
