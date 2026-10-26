"""Build the labelled dataset from PostgreSQL + the label file.

Reads telemetry and packet_features, keeps only rows that have a label, attaches the
nearest packet window (within 5 s, same rule as GET /merged) and writes a CSV.

Simulated data is for testing code only. Never report results from it.
"""
import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "ml" / "data"
TOLERANCE = pd.Timedelta(seconds=5)

TELEMETRY_FEATURES = [
    "rssi", "gateway_latency", "internet_latency", "dns_time", "packet_loss", "jitter",
    "http_time", "reconnect_count", "free_heap", "cpu_load", "dhcp_clients",
    "dhcp_leases_active", "dhcp_pool_free", "client_rssi_avg",
]
PACKET_FEATURES = [
    "dns_response_ms", "dns_fail_count", "tcp_retrans", "dhcp_offer_ms",
    "icmp_unreach", "pkt_rate", "byte_rate",
]


def main():
    parser = argparse.ArgumentParser(description="Build the labelled dataset")
    parser.add_argument("--labels", default=str(DATA / "sim_labels.csv"))
    parser.add_argument("--out", default=str(DATA / "sim_dataset.csv"))
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set. Check the .env file in the project root.")
    engine = create_engine(url)

    tel = pd.read_sql("SELECT * FROM telemetry", engine)
    pkt = pd.read_sql("SELECT * FROM packet_features", engine)
    labels = pd.read_csv(args.labels).drop_duplicates("telemetry_id")

    print(f"telemetry rows in DB: {len(tel)}   packet rows in DB: {len(pkt)}   labels: {len(labels)}")

    tel = tel.merge(labels[["telemetry_id", "fault_label"]], left_on="id", right_on="telemetry_id", how="inner")
    print(f"labelled telemetry rows kept: {len(tel)}")

    tel = tel.sort_values("received_at").reset_index(drop=True)
    pkt = pkt.sort_values("received_at").reset_index(drop=True)
    pkt["packet_time"] = pkt["received_at"]
    pkt = pkt.rename(columns={"id": "packet_id"})

    merged = pd.merge_asof(
        tel,
        pkt[["received_at", "packet_time", "packet_id"] + PACKET_FEATURES],
        on="received_at",
        direction="nearest",
        tolerance=TOLERANCE,
    )
    merged["packet_matched"] = merged["packet_id"].notna()
    merged["packet_gap_s"] = (merged["received_at"] - merged["packet_time"]).abs().dt.total_seconds()

    columns = (
        ["id", "received_at", "device_id", "fault_label"]
        + TELEMETRY_FEATURES
        + PACKET_FEATURES
        + ["packet_matched", "packet_gap_s"]
    )
    out = merged[columns]
    out.to_csv(args.out, index=False)

    print(f"\nSaved {len(out)} rows to {args.out}")
    print("\nRows per class:")
    print(out["fault_label"].value_counts().to_string())
    print(f"\nRows without a packet window: {int((~out['packet_matched']).sum())}")
    print("\nMissing values per column (only columns with any):")
    missing = out.isna().sum()
    print(missing[missing > 0].to_string() if (missing > 0).any() else "none")


if __name__ == "__main__":
    main()
