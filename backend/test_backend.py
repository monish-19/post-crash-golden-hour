"""
Post-Crash Golden Hour Optimizer
Phase ③: Backend automated verification suite.

This script uses the FastAPI TestClient to simulate two distinct critical crash cases:
  1. Critical Unconscious Patient: Driver is UNCONSCIOUS, requiring Trauma Level 1 and fast ETA.
  2. Stable Responsive Patient: Driver is RESPONSIVE, saving Level 1 resources for critical incidents.
It asserts hospital scores, dispatch decisions, and Green-Corridor preemption outputs.
"""

import json
import os
import sys
from fastapi.testclient import TestClient

# Ensure we can load app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.main import app


def test_routing_engine():
    client = TestClient(app)
    
    print("=" * 70)
    print("POST-CRASH GOLDEN HOUR OPTIMIZER - PHASE 3 VERIFICATION")
    print("=" * 70)

    # 1. Verify general REST endpoints
    print("\n[*] Testing base API status...")
    resp_base = client.get("/")
    assert resp_base.status_code == 200
    print(f"  + Base API: ONLINE (ws_connections: {resp_base.json().get('websocket_active_connections')})")

    print("\n[*] Testing Hospital Database API...")
    resp_hosp = client.get("/api/hospitals")
    assert resp_hosp.status_code == 200
    hospitals = resp_hosp.json()
    assert len(hospitals) == 4
    print(f"  + Digested {len(hospitals)} hospitals correctly.")
    for h in hospitals:
        print(f"    - {h['name']} | Trauma Level: {h['trauma_level']} | ER Beds: {h['available_er_beds']}")

    # --- CASE A: CRITICAL UNCONSCIOUS COLLISION ---
    print("\n[*] Simulating Case A: CRITICAL CRASH (Driver UNCONSCIOUS)...")
    critical_payload = {
        "timestamp": 1234567.8,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "speed_kmph": 0.0,
        "accel_x": 22.0,
        "accel_y": -65.0,
        "accel_z": 28.0,
        "isolated_g_force": 6.8322,
        "deceleration_delta_kmph": -80.0,
        "predicted_accident": 1,
        "driver_triage": {
            "ear_avg": 0.08,
            "mar": 0.56,
            "facial_asymmetry_index": 0.0833,
            "unresponsive_probability": 1.0,
            "suspected_intoxication_index": 0.0782,
            "driver_status_code": "UNCONSCIOUS"
        }
    }

    resp_critical = client.post("/api/telematics/crash", json=critical_payload)
    assert resp_critical.status_code == 200
    data_critical = resp_critical.json()
    
    assert data_critical["status"] == "CRITICAL_ACCIDENT_DECLARED"
    alert_c = data_critical["unified_alert"]
    
    # Assert Mercy General is selected (optimal score for Unconscious patient)
    hosp_c = alert_c["dispatch_decision"]["hospital_name"]
    eta_c = alert_c["dispatch_decision"]["paramedic_eta_minutes"]
    score_c = alert_c["dispatch_decision"]["dispatch_score"]
    
    print(f"  + Dispatched Hospital : {hosp_c}")
    print(f"  + Travel Time (Traffic ETA) : {eta_c} minutes")
    print(f"  + Dispatch Score : {score_c}")
    
    # Mercy General must win
    assert hosp_c == "Mercy General Hospital", f"FAIL: Expected Mercy General, got {hosp_c}"
    print("  [SUCCESS] Correctly routed UNCONSCIOUS victim to Mercy General (Trauma Level 1).")

    # Assert Green Corridor check-point parameters
    green_c = alert_c["green_corridor"]
    assert len(green_c) == 3
    print("  + Generated Green Corridor Intersections:")
    for gc in green_c:
        print(f"    - {gc['intersection_id']}: {gc['name']} | Status: {gc['preemption_status']} | Arrival: {gc['estimated_arrival_seconds']}s")
        assert gc["preemption_status"] == "PREEMPTING"
    print("  [SUCCESS] Symmetrical preemption intersections generated.")


    # --- CASE B: MINOR COLLISION (Driver RESPONSIVE) ---
    print("\n[*] Simulating Case B: MINOR COLLISION (Driver RESPONSIVE)...")
    minor_payload = {
        "timestamp": 1234580.0,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "speed_kmph": 25.0,
        "accel_x": 4.0,
        "accel_y": -15.0,
        "accel_z": 10.0,
        "isolated_g_force": 4.143,
        "deceleration_delta_kmph": -25.0,
        "predicted_accident": 1,
        "driver_triage": {
            "ear_avg": 0.58,
            "mar": 0.25,
            "facial_asymmetry_index": 0.0,
            "unresponsive_probability": 0.02,
            "suspected_intoxication_index": 0.01,
            "driver_status_code": "RESPONSIVE"
        }
    }

    resp_minor = client.post("/api/telematics/crash", json=minor_payload)
    assert resp_minor.status_code == 200
    data_minor = resp_minor.json()
    
    alert_m = data_minor["unified_alert"]
    hosp_m = alert_m["dispatch_decision"]["hospital_name"]
    score_m = alert_m["dispatch_decision"]["dispatch_score"]
    
    print(f"  + Dispatched Hospital : {hosp_m}")
    print(f"  + Dispatch Score : {score_m}")

    # City Memorial Hospital must win (Trauma Level 2, saving Level 1 capacities)
    assert hosp_m == "City Memorial Hospital", f"FAIL: Expected City Memorial, got {hosp_m}"
    print("  [SUCCESS] Correctly routed RESPONSIVE victim to City Memorial (Trauma Level 2) to preserve critical Level 1 bays.")

    # 4. Save backend verification logs
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend_verification_log.json")
    with open(log_file_path, "w") as f:
        json.dump({
            "status": "PASSED",
            "critical_case_dispatch": alert_c["dispatch_decision"],
            "minor_case_dispatch": alert_m["dispatch_decision"]
        }, f, indent=2)
    print(f"\n[*] Backend verification logs written to: {log_file_path}")
    print("=" * 70)


if __name__ == "__main__":
    test_routing_engine()
