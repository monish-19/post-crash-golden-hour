# 🚑 Post-Crash Golden Hour Optimizer

An intelligent, decoupled emergency response system combining **Edge AI Bio-Telemetry**, **Cloud-Based Multi-Attribute Hospital Allocation Routing**, and **Smart City IoT Traffic Signal Preemption** to maximize trauma survival rates within the critical post-accident "Golden Hour."

---

## 🚀 The Problem & Our Solution

During severe vehicular accidents, survival rates drop drastically if medical care isn't administered within the first 60 minutes (The Golden Hour). Standard emergency dispatch relies on manual calls and routes patients to the *nearest* hospital rather than the *most equipped* hospital, causing life-threatening delays.

**Our Platform Ecosystem:**
1. **Edge AI Monitoring:** Tracks real-time driver biometrics (Eye Aspect Ratio & Mouth Aspect Ratio) along with vehicular G-force data to instantaneously predict driver consciousness status.
2. **Cloud Routing Core:** Runs an asynchronous Multi-Attribute Utility Optimization algorithm matching patient condition variables to live hospital specialization levels and emergency bed availability.
3. **Smart City Integration:** Dynamically interfaces with urban traffic grids to establish an IoT Green Corridor, forcing traffic signals to green ahead of the en-route emergency vehicle.

---

## 🛠️ Tech Stack & Architecture

- **Backend:** FastAPI (Python), Pydantic v2 (Validation & Structuring), Uvicorn (Asynchronous Server Gateway)
- **Frontend Dashboard:** Streamlit (Analytical Real-time Emergency Monitoring Hub)
- **Data Terminal Logic:** Rich (ASCII Diagnostic Reporting Interface for Windows compatibility)
- **Data Protocols:** REST APIs, WebSockets (`websocket_endpoint`), JSON Ingestion Pipelines

---

## 📁 Repository Structure

```text
POST GOLDEN HR/
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI Application Core & WebSocket Logic
│   │   ├── routing.py              # Multi-Attribute Hospital Match Optimization
│   │   └── dashboard.py            # Streamlit Live Visual Command Center Interface
│   │
│   └── test_backend.py             # Automated Phase-3 Verification Pipeline
│
├── edge/                           # Vehicle Edge-Telemetry Simulation Units
├── frontend/                       # Legacy Web Client Layout assets
├── REQUIREMENTS.txt                # System Cloud Dependencies List
└── README.md                       # Documentation Manual
