# NetMind Architecture (Option A: AP + STA)

## Network layout
Client PC / phone --(joins ESP32's Wi-Fi, gets IP from ESP32's DHCP)--> ESP32
ESP32 --(joins home router as a client)--> Home router --> Internet

The ESP32 runs as an access point with a DHCP server (SoftAP) and as a
Wi-Fi client of the home router (STA), forwarding client traffic to the internet.

## Data flow
1. ESP32 --(HTTP POST, JSON, every 5 s)--> FastAPI backend
2. Packet collector on the client PC (tshark + pyshark, 5 s windows)
   --(HTTP POST)--> FastAPI backend
3. Backend merges both sources by time window and stores them in PostgreSQL
4. From the backend, each merged record goes to:
   - ML inference (anomaly, fault class, severity)
   - WebSocket push to the React dashboard
   - LangGraph agent (RAG + LLM) when a fault is detected, producing a
     root-cause explanation and fix steps

## Components
| Component | Role |
|---|---|
| ESP32 node | AP + DHCP server + network prober; sends telemetry |
| Packet collector | Wireshark/tshark capture on the client PC, extracts packet features |
| FastAPI backend | Receives, validates, merges, stores and serves data; runs the ML models |
| PostgreSQL | Stores telemetry, packet features, predictions and agent reports |
| ML models | Isolation Forest (anomaly), Random Forest/XGBoost (fault class), severity model |
| RAG store | Troubleshooting knowledge the agent searches (FAISS or Chroma) |
| LangGraph agent | Combines data, ML output and retrieved knowledge into an explanation |
| React dashboard | Shows live data, alerts and the root-cause analysis |

## Interfaces
- ESP32 to backend: REST (POST /telemetry)
- Packet collector to backend: REST (POST /packet-features)
- Backend to dashboard: REST for history, WebSocket for live updates

## Known limits
- Wireshark on Windows sees only the capturing PC's own traffic (plus
  broadcasts), so the PC is the "client under test".
- The ESP32 has limited throughput. Test traffic is kept modest.