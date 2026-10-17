# Project Scope

## Problem statement
(2-3 lines in your own words: why network faults are hard to diagnose manually,
and what NetMind automates. Write this yourself.)

## Objectives
1. Collect live network telemetry using an ESP32 node that also acts as an access point and DHCP server.
2. Capture and analyse packets with Wireshark/tshark to extract client-side features.
3. Detect abnormal behaviour using machine learning.
4. Classify the fault type and predict its severity.
5. Explain the likely root cause and suggest fixes using an AI agent with RAG.
6. Show everything on a live dashboard.

## In scope
- One ESP32 network (AP + STA) monitored from the client side
- The 9 fault classes in fault_classes.md
- A self-built dataset from controlled fault experiments

## Out of scope
- Enterprise or multi-site networks
- Capturing other devices' traffic (needs monitor mode)
- Automatic repair of faults (the system only diagnoses and recommends)

## Tech stack
ESP32 (Arduino/ESP-IDF), Wireshark/tshark, pyshark, Python, FastAPI,
PostgreSQL, scikit-learn, XGBoost, LangGraph, FAISS/Chroma, React,
Tailwind CSS, Docker