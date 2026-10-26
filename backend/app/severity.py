"""Rule-based severity for a detected fault.

There are no ground-truth severity labels, so severity is defined by explicit rules
(fault type plus measured values) instead of being learned. The thresholds are
proposals, to be reviewed and adjusted against real data.
"""

LEVELS = ["None", "Low", "Medium", "High", "Critical"]

BASE = {
    "normal": "None",
    "weak_signal": "Medium",
    "congestion": "Medium",
    "intermittent_loss": "Medium",
    "device_overload": "Medium",
    "dns_failure": "High",
    "dhcp_failure": "High",
    "gateway_failure": "Critical",
    "internet_failure": "Critical",
}


def _raise(level, steps=1):
    return LEVELS[min(LEVELS.index(level) + steps, len(LEVELS) - 1)]


def severity(fault, r):
    """Return (level, reasons) for a fault label and a merged record (a dict)."""
    level = BASE.get(fault, "Medium")
    if level == "None":
        return level, ["no fault detected"]

    def get(name, default=0.0):
        value = r.get(name)
        return default if value is None else value

    reasons = [f"{fault}: base level {level}"]
    escalate = []

    if fault == "weak_signal":
        if get("rssi", 0.0) < -85:
            escalate.append("rssi below -85 dBm")
        if get("packet_loss") > 15:
            escalate.append("packet loss above 15%")
    elif fault == "congestion":
        if get("packet_loss") > 5:
            escalate.append("packet loss above 5%")
        if get("internet_latency") > 400:
            escalate.append("internet latency above 400 ms")
    elif fault == "intermittent_loss":
        if get("packet_loss") > 30:
            escalate.append("packet loss above 30%")
    elif fault == "device_overload":
        if get("free_heap", 10**9) < 20000:
            escalate.append("free heap below 20 KB")
        if get("cpu_load") > 97:
            escalate.append("cpu load above 97%")

    if escalate:
        level = _raise(level)
        reasons += escalate
    return level, reasons
