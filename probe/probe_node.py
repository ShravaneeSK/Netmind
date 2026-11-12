"""NetMind software probe node.

Runs on a PC and measures its own network health every cycle, then posts one reading
to the backend in the format the ESP32 node would use (schema v2, source 1).
Fields that only an access-point node can measure (DHCP counters) are sent as 0.
Windows only: it uses the ping and netsh commands and assumes English output.
"""
import argparse
import re
import statistics
import subprocess
import threading
import time

import dns.resolver
import psutil
import requests

PING_TIME = re.compile(r"time[=<]\s*(\d+)\s*ms", re.IGNORECASE)


def ping(host, count, timeout_ms=1000):
    """Return (round-trip times in ms, number of lost probes) using the Windows ping command."""
    if not host:
        return [], count
    try:
        out = subprocess.run(
            ["ping", "-n", str(count), "-w", str(timeout_ms), host],
            capture_output=True, text=True,
            timeout=count * (timeout_ms / 1000 + 1) + 3,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return [], count
    rtts = [float(x) for x in PING_TIME.findall(out)]
    return rtts, max(0, count - len(rtts))


def default_gateway():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Sort-Object RouteMetric "
             "| Select-Object -First 1).NextHop"],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return None
    return out or None


def wifi_info():
    """Return (rssi in dBm or None, connected) from netsh. Quality % is converted approximately."""
    try:
        out = subprocess.run(["netsh", "wlan", "show", "interfaces"],
                             capture_output=True, text=True, timeout=5).stdout
    except (subprocess.SubprocessError, OSError):
        return None, False
    state = re.search(r"^\s*State\s*:\s*(\S+)", out, re.M)
    signal = re.search(r"^\s*Signal\s*:\s*(\d+)\s*%", out, re.M)
    connected = bool(state and state.group(1).lower() == "connected")
    rssi = (int(signal.group(1)) / 2 - 100) if signal else None
    return rssi, connected


def dns_time_ms(name):
    """DNS lookup time against the system DNS servers, no OS cache. -1 on any failure."""
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 2.0
    start = time.perf_counter()
    try:
        resolver.resolve(name, "A")
    except Exception:
        return -1.0
    return (time.perf_counter() - start) * 1000


def http_time_ms(url):
    start = time.perf_counter()
    try:
        requests.get(url, timeout=3).raise_for_status()
    except requests.RequestException:
        return -1.0
    return (time.perf_counter() - start) * 1000


def measure(gateway, args, state):
    results = {}

    def run(key, fn, *fn_args):
        results[key] = fn(*fn_args)

    threads = [
        threading.Thread(target=run, args=("gw", ping, gateway, 3)),
        threading.Thread(target=run, args=("net", ping, args.target, 5)),
        threading.Thread(target=run, args=("dns", dns_time_ms, args.dns_name)),
        threading.Thread(target=run, args=("http", http_time_ms, args.http_url)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    rssi, connected = wifi_info()
    if connected and not state["was_connected"]:
        state["reconnects"] += 1
    state["was_connected"] = connected
    rssi = round(rssi, 1) if rssi is not None else -100.0

    gw_rtts, _ = results["gw"]
    net_rtts, net_lost = results["net"]
    return {
        "device_id": args.device_id,
        "rssi": rssi,
        "gateway_latency": round(statistics.mean(gw_rtts), 2) if gw_rtts else -1,
        "internet_latency": round(statistics.mean(net_rtts), 2) if net_rtts else -1,
        "dns_time": round(results["dns"], 2),
        "packet_loss": round(100 * net_lost / 5, 1),
        "jitter": round(statistics.pstdev(net_rtts), 2) if len(net_rtts) > 1 else 0.0,
        "http_time": round(results["http"], 2),
        "reconnect_count": state["reconnects"],
        "free_heap": int(psutil.virtual_memory().available),
        "cpu_load": float(psutil.cpu_percent(interval=None)),
        "dhcp_clients": 0,
        "dhcp_leases_active": 0,
        "dhcp_pool_free": 0,
        "client_rssi_avg": rssi,
    }


def main():
    parser = argparse.ArgumentParser(description="NetMind software probe node")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--device-id", default="pc-probe")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between cycle starts")
    parser.add_argument("--cycles", type=int, default=0, help="number of cycles (0 = until Ctrl+C)")
    parser.add_argument("--target", default="8.8.8.8", help="host pinged for internet latency")
    parser.add_argument("--gateway", default=None, help="override the detected default gateway")
    parser.add_argument("--dns-name", default="example.com")
    parser.add_argument("--http-url", default="https://example.com")
    parser.add_argument("--dry-run", action="store_true", help="print readings, do not post")
    args = parser.parse_args()

    gateway = args.gateway or default_gateway()
    print(f"Probe '{args.device_id}': gateway={gateway}, target={args.target}, every {args.interval:g} s")
    if not gateway:
        print("Warning: no default gateway found, so gateway_latency will be -1.")

    rssi, connected = wifi_info()
    if rssi is None:
        print("Warning: no Wi-Fi signal information (wired connection, or non-English Windows). rssi is sent as -100.")
    state = {"reconnects": 0, "was_connected": connected}
    psutil.cpu_percent(interval=None)  # prime the CPU counter

    done = 0
    try:
        while True:
            started = time.time()
            reading = measure(gateway, args, state)
            done += 1
            summary = (
                f"#{done} rssi={reading['rssi']} gw={reading['gateway_latency']} "
                f"net={reading['internet_latency']} dns={reading['dns_time']} "
                f"http={reading['http_time']} loss={reading['packet_loss']}% "
                f"jitter={reading['jitter']} cpu={reading['cpu_load']}% reconnects={reading['reconnect_count']}"
            )
            if args.dry_run:
                print(summary)
            else:
                try:
                    r = requests.post(f"{args.url}/telemetry", json=reading, timeout=5)
                    r.raise_for_status()
                    print(f"{summary} -> id {r.json()['id']}")
                except requests.RequestException as e:
                    print(f"{summary} -> POST failed: {e}")
            if args.cycles and done >= args.cycles:
                break
            time.sleep(max(0.0, args.interval - (time.time() - started)))
    except KeyboardInterrupt:
        print("Stopping.")


if __name__ == "__main__":
    main()
