"""NetMind simulator: fake ESP32 telemetry + packet features for pipeline testing.

Simulated data is for testing code only. It must never be used for reported results.
"""
import argparse
import csv
import random
import time
from datetime import datetime
from pathlib import Path

import requests

FAULTS = [
    "normal", "weak_signal", "congestion", "dns_failure", "gateway_failure",
    "internet_failure", "device_overload", "intermittent_loss", "dhcp_failure",
]


def n(mu, sigma, lo=None, hi=None):
    """Gaussian value clamped to [lo, hi]."""
    x = random.gauss(mu, sigma)
    if lo is not None:
        x = max(lo, x)
    if hi is not None:
        x = min(hi, x)
    return round(x, 2)


def normal_reading():
    tel = {
        "device_id": "esp32-sim",
        "rssi": n(-55, 4, -66),
        "gateway_latency": n(4, 1.5, 1, 9),
        "internet_latency": n(30, 8, 15, 60),
        "dns_time": n(25, 8, 5, 90),
        "packet_loss": 0.0,
        "jitter": n(2, 0.8, 0.2),
        "http_time": n(250, 60, 100, 480),
        "reconnect_count": 0,
        "free_heap": int(n(210000, 3000, 150000)),
        "cpu_load": n(12, 3, 1, 40),
        "dhcp_clients": 1,
        "dhcp_leases_active": 1,
        "dhcp_pool_free": 9,
        "client_rssi_avg": n(-48, 3, -66),
    }
    pkt = {
        "dns_response_ms": n(25, 8, 5, 90),
        "dns_fail_count": 0,
        "tcp_retrans": random.randint(0, 2),
        "dhcp_offer_ms": n(35, 10, 10, 90),
        "icmp_unreach": 0,
        "pkt_rate": n(120, 20, 40),
        "byte_rate": n(85000, 12000, 10000),
    }
    return tel, pkt


def generate(fault):
    tel, pkt = normal_reading()

    if fault == "weak_signal":
        tel.update(rssi=n(-82, 3, -95, -76), client_rssi_avg=n(-80, 3, -95, -76),
                   gateway_latency=n(25, 10, 8), internet_latency=n(90, 30, 40),
                   jitter=n(15, 5, 5), packet_loss=n(8, 4, 1, 25),
                   http_time=n(900, 300, 400), reconnect_count=random.randint(0, 3))
        pkt.update(tcp_retrans=random.randint(5, 15))

    elif fault == "congestion":
        tel.update(gateway_latency=n(180, 40, 120), internet_latency=n(250, 60, 160),
                   jitter=n(30, 8, 12), packet_loss=n(2, 1, 0, 6),
                   http_time=n(1500, 400, 700))
        pkt.update(tcp_retrans=random.randint(10, 30), pkt_rate=n(600, 100, 300),
                   byte_rate=n(900000, 150000, 400000))

    elif fault == "dns_failure":
        tel.update(dns_time=-1, http_time=-1)
        pkt.update(dns_response_ms=-1, dns_fail_count=random.randint(3, 8))

    elif fault == "gateway_failure":
        tel.update(gateway_latency=-1, internet_latency=-1, dns_time=-1, http_time=-1,
                   packet_loss=n(98, 1.5, 90, 100), jitter=0)
        pkt.update(dns_response_ms=-1, dns_fail_count=random.randint(2, 6),
                   icmp_unreach=random.randint(2, 8), pkt_rate=n(8, 3, 1),
                   byte_rate=n(1500, 500, 200))

    elif fault == "internet_failure":
        tel.update(internet_latency=-1, dns_time=-1, http_time=-1,
                   packet_loss=n(50, 10, 25, 80))
        pkt.update(dns_response_ms=-1, dns_fail_count=random.randint(2, 6),
                   icmp_unreach=random.randint(1, 5), pkt_rate=n(30, 10, 5))

    elif fault == "device_overload":
        tel.update(free_heap=int(n(40000, 8000, 10000)), cpu_load=n(92, 4, 80, 100),
                   gateway_latency=n(60, 30, 15), internet_latency=n(120, 60, 40),
                   jitter=n(25, 10, 8), dns_time=n(80, 40, 20),
                   http_time=n(1200, 500, 500))

    elif fault == "intermittent_loss":
        tel.update(packet_loss=round(random.uniform(10, 50), 2),
                   gateway_latency=n(30, 25, 3), internet_latency=n(120, 70, 25),
                   jitter=n(40, 15, 10), http_time=n(1000, 500, 300),
                   reconnect_count=random.randint(0, 2))
        pkt.update(tcp_retrans=random.randint(8, 25))

    elif fault == "dhcp_failure":
        if random.random() < 0.5:  # address pool exhausted
            tel.update(dhcp_clients=10, dhcp_leases_active=10, dhcp_pool_free=0)
        else:  # DHCP service not answering
            tel.update(dhcp_clients=0, dhcp_leases_active=0, client_rssi_avg=-1)
        pkt.update(dhcp_offer_ms=-1, pkt_rate=n(15, 5, 1), byte_rate=n(3000, 1000, 200))

    return tel, pkt


def main():
    parser = argparse.ArgumentParser(description="NetMind data simulator")
    parser.add_argument("--fault", default="normal", choices=FAULTS + ["all"])
    parser.add_argument("--count", type=int, default=20, help="readings per fault")
    parser.add_argument("--interval", type=float, default=0.5, help="seconds between readings")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    out_dir = Path(__file__).resolve().parents[1] / "ml" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    label_file = out_dir / "sim_labels.csv"
    new_file = not label_file.exists()

    faults = FAULTS if args.fault == "all" else [args.fault]
    sent = failed = 0

    with open(label_file, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["telemetry_id", "fault_label", "sent_at"])

        for fault in faults:
            for _ in range(args.count):
                tel, pkt = generate(fault)
                try:
                    r = requests.post(f"{args.url}/packet-features", json=pkt, timeout=5)
                    r.raise_for_status()
                    r = requests.post(f"{args.url}/telemetry", json=tel, timeout=5)
                    r.raise_for_status()
                    writer.writerow([r.json()["id"], fault, datetime.now().isoformat()])
                    f.flush()
                    sent += 1
                except requests.RequestException as e:
                    failed += 1
                    print(f"FAILED ({fault}): {e}")
                time.sleep(args.interval)
            print(f"{fault}: done")

    print(f"Finished. Sent {sent}, failed {failed}. Labels in {label_file}")


if __name__ == "__main__":
    main()
    