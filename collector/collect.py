"""NetMind packet collector.

Captures this PC's traffic with tshark in 5-second windows, generates a little probe
traffic in each window, extracts the 7 packet features (schema v2, Source 2) and
posts them to the backend. Capture files are deleted right after analysis.

DNS features count only ordinary DNS on port 53. Multicast DNS (.local, port 5353)
and reverse (.arpa) lookups are ignored, because they are background noise.
"""
import argparse
import shutil
import statistics
import subprocess
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path

import requests

WINDOW = 5
GRACE = 1.0  # DNS queries sent in the last second are probably answered in the next window
DEFAULT_TSHARK = r"C:\Program Files\Wireshark\tshark.exe"

FIELDS = [
    "frame.len",
    "frame.time_relative",
    "dns.flags.response",
    "dns.flags.rcode",
    "dns.qry.name",
    "dns.time",
    "tcp.analysis.retransmission",
    "icmp.type",
    "udp.srcport",
    "udp.dstport",
    "tcp.srcport",
    "tcp.dstport",
]


def find_tshark():
    found = shutil.which("tshark")
    if found:
        return found
    return DEFAULT_TSHARK if Path(DEFAULT_TSHARK).exists() else None


def start_capture(tshark, iface, path):
    return subprocess.Popen(
        [tshark, "-i", iface, "-a", f"duration:{WINDOW}", "-w", str(path), "-q"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def probe_traffic(name):
    """Small, predictable traffic so every window has DNS and TCP to measure.

    Waits 2 s so the capture is certainly recording (tshark takes a moment to start),
    then sends two DNS lookups and one web request.
    """
    time.sleep(2.0)
    for _ in range(2):
        try:
            subprocess.run(["nslookup", name], capture_output=True, timeout=5)
        except (subprocess.SubprocessError, OSError):
            pass
        time.sleep(0.3)
    try:
        requests.get(f"https://{name}", timeout=2)
    except requests.RequestException:
        pass


def analyse(tshark, pcap, debug=False):
    """Extract the 7 packet features from one capture window."""
    cmd = [tshark, "-r", str(pcap), "-T", "fields", "-E", "separator=|", "-E", "occurrence=f"]
    for field in FIELDS:
        cmd += ["-e", field]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[:300])

    packets = total_bytes = 0
    errors = retrans = unreach = 0
    dns_times = []
    q_names = Counter()  # queries seen, per name
    r_names = Counter()  # responses seen, per name

    for line in result.stdout.splitlines():
        parts = line.split("|")
        parts += [""] * (len(FIELDS) - len(parts))
        (length, t_rel, is_resp, rcode, name, dns_time,
         retrans_flag, icmp_type, usrc, udst, tsrc, tdst) = parts[: len(FIELDS)]

        packets += 1
        total_bytes += int(length or 0)

        lname = name.lower()
        is_port_53 = "53" in (usrc, udst, tsrc, tdst)
        if name and is_port_53 and "arpa" not in lname and not lname.endswith(".local"):
            if is_resp in ("1", "True", "true"):
                r_names[lname] += 1
                if rcode not in ("", "0"):
                    errors += 1
                if dns_time:
                    dns_times.append(float(dns_time) * 1000)
            else:
                try:
                    late = float(t_rel) > WINDOW - GRACE
                except ValueError:
                    late = False
                if not late:
                    q_names[lname] += 1

        if retrans_flag:
            retrans += 1
        if icmp_type == "3":
            unreach += 1

    unanswered_by_name = {n: q - r_names[n] for n, q in q_names.items() if q > r_names[n]}
    unanswered = sum(unanswered_by_name.values())

    if debug:
        shown = dict(list(unanswered_by_name.items())[:3])
        print(
            f"  debug: packets={packets} dns_queries={sum(q_names.values())} "
            f"dns_responses={sum(r_names.values())} dns_errors={errors} "
            f"unanswered={unanswered} {shown}"
        )

    return {
        "dns_response_ms": round(statistics.median(dns_times), 2) if dns_times else -1,
        "dns_fail_count": errors + unanswered,
        "tcp_retrans": retrans,
        "dhcp_offer_ms": 0,  # 0 = no DHCP exchange observed (measured from Stage 10)
        "icmp_unreach": unreach,
        "pkt_rate": round(packets / WINDOW, 2),
        "byte_rate": round(total_bytes / WINDOW, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="NetMind packet collector")
    parser.add_argument("--interface", default="Wi-Fi", help='tshark interface name or number (see "tshark -D")')
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--windows", type=int, default=0, help="number of windows (0 = run until Ctrl+C)")
    parser.add_argument("--probe-name", default="example.com")
    parser.add_argument("--no-probe", action="store_true", help="do not generate probe traffic")
    parser.add_argument("--dry-run", action="store_true", help="print features, do not post")
    parser.add_argument("--debug", action="store_true", help="print DNS counters per window")
    args = parser.parse_args()

    tshark = find_tshark()
    if not tshark:
        print("tshark not found. Install Wireshark or add it to PATH.")
        return

    tmp = Path(tempfile.mkdtemp(prefix="netmind_"))
    index = 0
    cap = path = None

    def begin(i):
        p = tmp / f"win_{i}.pcapng"
        c = start_capture(tshark, args.interface, p)
        if not args.no_probe:
            threading.Thread(target=probe_traffic, args=(args.probe_name,), daemon=True).start()
        return c, p

    print(f"Collecting {WINDOW}-second windows on '{args.interface}'. Ctrl+C to stop.")
    try:
        cap, path = begin(index)
        while True:
            cap.wait()
            if cap.returncode != 0 or not path.exists():
                print(f'Capture failed. Check the interface name with "tshark -D" (tried "{args.interface}").')
                break

            finished = path
            index += 1
            last = bool(args.windows) and index >= args.windows
            if not last:
                cap, path = begin(index)  # next capture runs while we analyse this one

            features = None
            try:
                features = analyse(tshark, finished, args.debug)
            except (RuntimeError, subprocess.SubprocessError) as e:
                print(f"Analysis failed: {e}")
            finally:
                finished.unlink(missing_ok=True)

            if features:
                if args.dry_run:
                    print(features)
                else:
                    try:
                        r = requests.post(f"{args.url}/packet-features", json=features, timeout=5)
                        r.raise_for_status()
                        print(f"window {index}: posted id={r.json()['id']} {features}")
                    except requests.RequestException as e:
                        print(f"window {index}: POST failed: {e}")

            if last:
                break
    except KeyboardInterrupt:
        print("Stopping.")
        if cap and cap.poll() is None:
            cap.terminate()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()