from datetime import timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from . import models, schemas

WINDOW = timedelta(seconds=5)

PACKET_FIELDS = [
    "dns_response_ms",
    "dns_fail_count",
    "tcp_retrans",
    "dhcp_offer_ms",
    "icmp_unreach",
    "pkt_rate",
    "byte_rate",
]


def merged_records(db: Session, limit: int = 50) -> list[dict]:
    """Attach the nearest packet-feature row (within 5 s) to each telemetry row."""
    readings = (
        db.query(models.Telemetry)
        .order_by(desc(models.Telemetry.received_at))
        .limit(limit)
        .all()
    )
    if not readings:
        return []

    start = min(r.received_at for r in readings) - WINDOW
    end = max(r.received_at for r in readings) + WINDOW
    packets = (
        db.query(models.PacketFeatures)
        .filter(
            models.PacketFeatures.received_at >= start,
            models.PacketFeatures.received_at <= end,
        )
        .all()
    )

    records = []
    for r in readings:
        record = schemas.TelemetryOut.model_validate(r).model_dump()
        nearest, gap = None, None
        for p in packets:
            d = abs((p.received_at - r.received_at).total_seconds())
            if d <= WINDOW.total_seconds() and (gap is None or d < gap):
                nearest, gap = p, d

        record["packet_matched"] = nearest is not None
        record["packet_gap_s"] = round(gap, 3) if gap is not None else None
        for name in PACKET_FIELDS:
            record[name] = getattr(nearest, name) if nearest is not None else None
        records.append(record)
    return records