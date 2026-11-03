"""Run the agent on one reading per fault class and print a short report."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.database import SessionLocal  # noqa: E402
from backend.app.diagnose import check_facts, run_agent  # noqa: E402


def last_ids():
    ids = {}
    with open(ROOT / "ml" / "data" / "sim_labels.csv", newline="") as f:
        for row in csv.DictReader(f):
            ids[row["fault_label"]] = int(row["telemetry_id"])
    return ids


def main():
    db = SessionLocal()
    try:
        results = {}
        print(f"{'expected':18} {'predicted':18} {'severity':9} {'verified':9} steps")
        for expected, tid in last_ids().items():
            r = run_agent(db, tid)
            results[expected] = r
            steps = " > ".join(r["trace"])
            print(f"{expected:18} {r['fault_label']:18} {r['severity']:9} {str(r['verified']):9} {steps}")

        print("\n=== Full explanation: dns_failure ===")
        print(results["dns_failure"]["explanation"])
        print("\nSources:", ", ".join(results["dns_failure"]["sources"]))
    finally:
        db.close()

    print("\n=== Consistency check demo ===")
    print("correct claim:", check_facts("- dns_time = 5 ms", {"dns_time": 5.0}))
    print("wrong claim:  ", check_facts("- dns_time = 500 ms", {"dns_time": 5.0}))


if __name__ == "__main__":
    main()
