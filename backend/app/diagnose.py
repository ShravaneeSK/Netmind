"""NetMind diagnosis agent (LangGraph).

Workflow: fetch -> predict -> retrieve -> compose -> verify -> (fallback)

The models and rules decide WHAT the fault is and how severe it is. This module only
explains. The explanation is rule-based: it quotes the real readings, adds the matching
notes from the knowledge base (looked up by fault tag) and is verified so that every
"field = number" claim matches the record. No language model is needed. A language-model
rewrite step could be added later between compose and verify; verify would then catch
any number it gets wrong.
"""
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from .predictor import build_record, predict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # so "rag" can be imported

UNITS = {
    "rssi": "dBm", "client_rssi_avg": "dBm",
    "gateway_latency": "ms", "internet_latency": "ms", "dns_time": "ms",
    "http_time": "ms", "jitter": "ms", "dns_response_ms": "ms", "dhcp_offer_ms": "ms",
    "packet_loss": "%", "cpu_load": "%",
    "free_heap": "bytes", "pkt_rate": "packets/s", "byte_rate": "bytes/s",
}
FAILABLE = {"gateway_latency", "internet_latency", "dns_time", "http_time",
            "dns_response_ms", "dhcp_offer_ms"}

EVIDENCE_FIELDS = {
    "normal": ["rssi", "gateway_latency", "internet_latency", "dns_time", "packet_loss"],
    "weak_signal": ["rssi", "client_rssi_avg", "gateway_latency", "packet_loss", "jitter"],
    "congestion": ["gateway_latency", "internet_latency", "pkt_rate", "tcp_retrans", "rssi"],
    "dns_failure": ["dns_time", "dns_response_ms", "dns_fail_count",
                    "gateway_latency", "internet_latency"],
    "gateway_failure": ["gateway_latency", "internet_latency", "packet_loss",
                        "pkt_rate", "icmp_unreach"],
    "internet_failure": ["gateway_latency", "internet_latency", "dns_time", "packet_loss"],
    "device_overload": ["cpu_load", "free_heap", "rssi", "gateway_latency"],
    "intermittent_loss": ["packet_loss", "jitter", "tcp_retrans", "gateway_latency"],
    "dhcp_failure": ["dhcp_offer_ms", "dhcp_pool_free", "dhcp_clients", "pkt_rate"],
}

GUIDANCE_SECTIONS = [
    ("Likely causes", "likely causes"),
    ("What to check first", "how to check"),
    ("How to fix it", "how to fix"),
]


class AgentState(TypedDict, total=False):
    db: Any
    telemetry_id: int
    record: dict
    prediction: dict
    notes: list
    facts: str
    guidance: str
    explanation: str
    verified: bool
    problems: list
    trace: list


def fmt(name, value):
    """Format one reading the same way everywhere, so claims can be checked."""
    if value is None:
        return f"{name} = not available"
    number = float(value)
    shown = int(number) if number.is_integer() else round(number, 1)
    unit = UNITS.get(name, "")
    text = f"{name} = {shown}" + (f" {unit}" if unit else "")
    if shown == -1 and name in FAILABLE:
        text += " (measurement failed)"
    if name == "dhcp_offer_ms" and shown == 0:
        text += " (no DHCP exchange seen)"
    return text


def check_facts(facts, record):
    """Every 'field = number' claim in the text must match the record."""
    problems = []
    for name, value in re.findall(r"([a-z_]+) = (-?\d+(?:\.\d+)?)", facts):
        if name not in record or record[name] is None:
            problems.append(f"{name} is not in the record")
        elif abs(float(value) - float(record[name])) > 0.06:
            problems.append(f"{name} = {value} does not match the record ({record[name]})")
    return problems


def _step(state, name):
    return state.get("trace", []) + [name]


def fetch_node(state):
    return {"record": build_record(state["db"], state["telemetry_id"]),
            "trace": _step(state, "fetch")}


def predict_node(state):
    return {"prediction": predict(state["record"]), "trace": _step(state, "predict")}


def retrieve_node(state):
    fault = state["prediction"]["fault_label"]
    try:
        from rag.search import notes_for

        notes = notes_for(fault)
        label = "retrieve"
    except Exception as e:  # knowledge base missing or broken: keep going without notes
        notes = []
        label = f"retrieve (no notes: {type(e).__name__})"
    return {"notes": notes, "trace": _step(state, label)}


def compose_node(state):
    pred, rec = state["prediction"], state["record"]
    fault = pred["fault_label"]

    lines = [f"Detected: {fault} (severity {pred['severity']}, confidence {pred['confidence']:.0%})."]
    runners = [(k, v) for k, v in pred["top_classes"].items() if k != fault and v >= 0.15]
    if runners:
        lines.append("Also considered: " + ", ".join(f"{k} ({v:.0%})" for k, v in runners) + ".")
    if pred["is_anomaly"]:
        lines.append("The anomaly detector flagged this reading as unusual compared with normal behaviour.")
    lines += ["", "What the data shows:"]
    for name in EVIDENCE_FIELDS.get(fault, EVIDENCE_FIELDS["normal"]):
        lines.append("- " + fmt(name, rec.get(name)))
    lines += ["", "Why this severity:"] + ["- " + r for r in pred["reasons"]]
    facts = "\n".join(lines)

    sections = {}
    for note in state.get("notes", []):
        text = note["text"]
        sections[note["section"]] = text.split("\n", 1)[1].strip() if "\n" in text else text
    parts = [f"{title}:\n{sections[key]}" for title, key in GUIDANCE_SECTIONS if key in sections]
    guidance = "\n\n".join(parts) if parts else (
        "No troubleshooting notes were available. Run python rag/ingest.py to build the knowledge base."
    )
    return {"facts": facts, "guidance": guidance, "trace": _step(state, "compose")}


def verify_node(state):
    problems = check_facts(state["facts"], state["record"])
    update = {"problems": problems, "verified": not problems, "trace": _step(state, "verify")}
    if not problems:
        update["explanation"] = state["facts"] + "\n\n" + state["guidance"]
    return update


def fallback_node(state):
    pred = state["prediction"]
    text = (
        f"Detected: {pred['fault_label']} (severity {pred['severity']}).\n"
        "The detailed explanation failed its consistency check and was withheld.\n"
        "Problems: " + "; ".join(state["problems"])
    )
    return {"explanation": text, "trace": _step(state, "fallback")}


@lru_cache(maxsize=1)
def _graph():
    g = StateGraph(AgentState)
    g.add_node("fetch", fetch_node)
    g.add_node("predict", predict_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("compose", compose_node)
    g.add_node("verify", verify_node)
    g.add_node("fallback", fallback_node)
    g.set_entry_point("fetch")
    g.add_edge("fetch", "predict")
    g.add_edge("predict", "retrieve")
    g.add_edge("retrieve", "compose")
    g.add_edge("compose", "verify")
    g.add_conditional_edges("verify", lambda s: "ok" if s["verified"] else "bad",
                            {"ok": END, "bad": "fallback"})
    g.add_edge("fallback", END)
    return g.compile()


def run_agent(db, telemetry_id):
    final = _graph().invoke({"db": db, "telemetry_id": telemetry_id, "trace": []})
    pred = final["prediction"]
    return {
        "telemetry_id": telemetry_id,
        "fault_label": pred["fault_label"],
        "severity": pred["severity"],
        "confidence": pred["confidence"],
        "is_anomaly": pred["is_anomaly"],
        "top_classes": pred["top_classes"],
        "explanation": final["explanation"],
        "verified": final["verified"],
        "problems": final.get("problems", []),
        "sources": [f"{pred['fault_label']}/{n['section']}" for n in final.get("notes", [])],
        "trace": final["trace"],
    }
