"""Failure-mode tests for the diagnosis agent. Each case prints PASS or FAIL."""
import csv
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app import models  # noqa: E402
from backend.app.database import SessionLocal  # noqa: E402
from backend.app.diagnose import run_agent  # noqa: E402
from backend.app.predictor import NoPacketWindow, TelemetryNotFound  # noqa: E402

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))


def dns_failure_id():
    last = None
    with open(ROOT / "ml" / "data" / "sim_labels.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["fault_label"] == "dns_failure":
                last = int(row["telemetry_id"])
    return last


def main():
    db = SessionLocal()
    try:
        tid = dns_failure_id()

        # 1. Unknown id
        try:
            run_agent(db, 99999999)
            check("unknown id raises TelemetryNotFound", False, "no error was raised")
        except TelemetryNotFound:
            check("unknown id raises TelemetryNotFound", True)

        # 2. A reading with no packet window nearby (temporary row, deleted afterwards)
        row = models.Telemetry(
            device_id="test-no-packet", rssi=-60, gateway_latency=4, internet_latency=30,
            dns_time=20, packet_loss=0, jitter=2, http_time=200, reconnect_count=0,
            free_heap=200000, cpu_load=10, dhcp_clients=1, dhcp_leases_active=1,
            dhcp_pool_free=9, client_rssi_avg=-50,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        try:
            run_agent(db, row.id)
            check("no packet window raises NoPacketWindow", False,
                  "no error (a collector may be running)")
        except NoPacketWindow:
            check("no packet window raises NoPacketWindow", True)
        finally:
            db.delete(row)
            db.commit()

        # 3. Knowledge base broken: the agent must still answer
        with patch("rag.search.notes_for", side_effect=RuntimeError("index gone")):
            r = run_agent(db, tid)
        ok = (
            r["fault_label"] == "dns_failure"
            and r["verified"]
            and any("no notes" in step for step in r["trace"])
            and "No troubleshooting notes" in r["explanation"]
        )
        check("broken knowledge base: still answers and says notes are missing", ok)

        # 4. A wrong number in the explanation must be caught and withheld
        with patch("backend.app.diagnose.fmt",
                   side_effect=lambda n, v: f"{n} = {int(float(v or 0)) + 1000}"):
            r = run_agent(db, tid)
        ok = (
            r["verified"] is False
            and r["trace"][-1] == "fallback"
            and "withheld" in r["explanation"]
            and len(r["problems"]) > 0
        )
        check("wrong numbers: verify fails and the fallback withholds the text", ok,
              f"{len(r['problems'])} problems found")
        check("wrong numbers: fault label and severity are unchanged",
              r["fault_label"] == "dns_failure" and r["severity"] == "High")
    finally:
        db.close()

    print(f"\n{sum(results)}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
