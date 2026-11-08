# NetMind

Agentic AI-based network monitoring, troubleshooting and root-cause analysis.

An ESP32 node and a packet collector (Wireshark/tshark) feed a FastAPI backend with PostgreSQL. ML models (a Random Forest fault classifier and an Isolation Forest anomaly detector) and a rule-based severity module classify each reading. A LangGraph agent fetches troubleshooting notes from a ChromaDB knowledge base and writes an explanation that is checked against the measured values. A React dashboard shows live status, history and diagnoses.

## Status

- Done: backend, simulator, packet collector, ML pipeline, knowledge base, diagnosis agent, dashboard.
- Pending: ESP32 firmware (access point, DHCP server, probes) and real-data experiments with final evaluation.
- All data so far is SIMULATED. Model scores on simulated data only show that the code works. They are not results.

## Requirements

Windows 10/11, Python 3.11 or 3.12, Node.js 20+, Docker Desktop. Wireshark with Npcap is needed only for the packet collector. Plan for about 8 GB of RAM and close other heavy apps.

## Setup from a fresh clone

Run these in PowerShell, from the project folder.

1. Python environment

        python -m venv venv
        venv\Scripts\activate
        pip install -r requirements.txt

   If activation is blocked, run: Set-ExecutionPolicy -Scope Process RemoteSigned

2. Settings. Create a file named .env in the project folder containing this single line (see .env.example). The .env file is git-ignored. Use a different password anywhere other than your own PC.

        DATABASE_URL=postgresql+psycopg2://netmind:netmind123@127.0.0.1:5432/netmind

3. Database

        docker run --name netmind-db -e POSTGRES_USER=netmind -e POSTGRES_PASSWORD=netmind123 -e POSTGRES_DB=netmind -p 5432:5432 -d postgres:16

4. Dashboard packages

        cd frontend
        npm install
        cd ..

5. Knowledge base. The first run downloads a small embedding model.

        python rag\ingest.py

6. Models. They are not stored in Git, so train them. Start the backend in one terminal:

        cd backend
        uvicorn app.main:app

   Then, in a second terminal in the project folder:

        python simulator\simulate.py --fault all --count 30 --interval 0.2
        python ml\build_dataset.py
        python ml\train.py

   Stop the backend with Ctrl+C when this is done.

## Run

    powershell -ExecutionPolicy Bypass -File scripts\start_netmind.ps1

This starts the database container, the backend and the dashboard, then opens http://localhost:5173. To stop:

    powershell -ExecutionPolicy Bypass -File scripts\stop_netmind.ps1

Add -Db to also stop the database container. The backend runs without auto-reload, so restart it after changing backend code.

## Demo

The buttons in the demo bar inject one simulated fault each. These rows use device_id "demo", are never written to the label file and are not measurements. Set DEMO_MODE=0 in .env to switch the demo endpoint off.

## Packet collector (needs Wireshark and Npcap)

Find your interface with: tshark -D

    python collector\collect.py --interface Wi-Fi

Use --dry-run to print the features without sending them.

## Tests

    python agent\test_agent.py
    python agent\test_failures.py
    python rag\test_retrieval.py

## Folders

- backend: FastAPI app, models, prediction, severity rules, diagnosis agent
- frontend: React and Tailwind dashboard
- simulator: fake ESP32 readings (for testing only)
- collector: packet feature extraction with tshark
- ml: dataset builder, training and evaluation scripts
- rag: knowledge documents, index builder and search
- agent: agent tests
- scripts: start and stop scripts
- docs: telemetry schema, fault classes, architecture, scope

## Notes

- Severity thresholds in backend/app/severity.py are proposals to be reviewed against real data.
- Never commit .env, packet captures or trained models.
