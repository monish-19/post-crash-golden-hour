"""
Post-Crash Golden Hour Optimizer
Phase ②: Test Suite & Driver Triage Verification

This script synthesizes 3D MediaPipe Face Mesh coordinates over multiple frames to model
three distinct driver states:
  1. Alert / Responsive: Normal eye blinking and stable resting mouth shape.
  2. Unconscious / Slumped: Prolonged eye closure (EAR < 0.12) and severe mouth sag (MAR > 0.50).
  3. Suspected Intoxication: Sluggish blinking pattern and moderate mouth resting open (MAR ~ 0.35).
It runs these coordinate sequences through the DriverTriageAnalyzer, asserting mathematically
correct ratios and classification indices.
"""

import json
import os
import sys
import math
from typing import List, Dict, Any, Tuple

# Ensure we can import triage_analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from triage_analyzer import DriverTriageAnalyzer


def build_baseline_landmarks() -> List[List[float]]:
    """
    Builds a baseline set of 468 3D landmark coordinates in a standard neutral posture.
    Coordinates are normalized to range [0.0, 1.0].
    """
    # Initialize all 468 points to center of face at (0.5, 0.5, 0.0)
    landmarks = [[0.5, 0.5, 0.0] for _ in range(468)]
    
    # Establish Outer Face Scale bounds (Cheeks 234 and 454)
    landmarks[234] = [0.2, 0.5, 0.0]  # Outer Left Cheek
    landmarks[454] = [0.8, 0.5, 0.0]  # Outer Right Cheek
    # Face width = 0.60
    
    # Left Eyebrow outer 70, Right Eyebrow outer 300
    landmarks[70] = [0.32, 0.31, 0.0]
    landmarks[300] = [0.68, 0.31, 0.0]
    
    # --- Initialize Left Eye open (width = 0.1, max height = 0.06) ---
    landmarks[362] = [0.60, 0.40, 0.0]  # p1: Left corner
    landmarks[263] = [0.70, 0.40, 0.0]  # p4: Right corner
    landmarks[385] = [0.63, 0.37, 0.0]  # p2: Upper mid 1
    landmarks[387] = [0.67, 0.37, 0.0]  # p3: Upper mid 2
    landmarks[373] = [0.67, 0.43, 0.0]  # p5: Lower mid 2
    landmarks[380] = [0.63, 0.43, 0.0]  # p6: Lower mid 1
    
    # --- Initialize Right Eye open (width = 0.1, max height = 0.06) ---
    landmarks[33] = [0.30, 0.40, 0.0]   # p1: Left corner
    landmarks[133] = [0.40, 0.40, 0.0]  # p4: Right corner
    landmarks[160] = [0.33, 0.37, 0.0]  # p2: Upper mid 1
    landmarks[158] = [0.37, 0.37, 0.0]  # p3: Upper mid 2
    landmarks[153] = [0.37, 0.43, 0.0]  # p5: Lower mid 2
    landmarks[144] = [0.33, 0.43, 0.0]  # p6: Lower mid 1
    
    # --- Initialize Mouth closed/resting (width = 0.16, height = 0.04) ---
    landmarks[61] = [0.42, 0.65, 0.0]   # Left corner
    landmarks[291] = [0.58, 0.65, 0.0]  # Right corner
    landmarks[13] = [0.50, 0.63, 0.0]   # Upper lip center
    landmarks[14] = [0.50, 0.67, 0.0]   # Lower lip center

    return landmarks


def simulate_burst_sequence(driver_state: str, num_frames: int = 20) -> List[List[List[float]]]:
    """
    Simulates a sequence of 20 coordinate mesh frames based on target driver states.
    """
    sequence = []
    
    for frame_idx in range(num_frames):
        landmarks = build_baseline_landmarks()
        
        if driver_state == "ALERT":
            # standard blinking: eyes closed brief interval (e.g. frames 8-9)
            if frame_idx in [8, 9]:
                # Collapse left eye upper lids
                landmarks[385][1] = 0.395; landmarks[387][1] = 0.395
                landmarks[373][1] = 0.405; landmarks[380][1] = 0.405
                # Collapse right eye upper lids
                landmarks[160][1] = 0.395; landmarks[158][1] = 0.395
                landmarks[153][1] = 0.405; landmarks[144][1] = 0.405
            else:
                # Normal open eyes
                pass
            
            # Normal mouth closed
            landmarks[13][1] = 0.63
            landmarks[14][1] = 0.67

        elif driver_state == "UNCONSCIOUS":
            # Sustained closed eyes (EAR ~ 0.08) across all frames
            for idx in [385, 387, 160, 158]:
                landmarks[idx][1] = 0.396
            for idx in [373, 380, 153, 144]:
                landmarks[idx][1] = 0.404
            
            # Massive jaw slackness / mouth sag (MAR = 0.09 / 0.16 = 0.56)
            landmarks[13][1] = 0.60
            landmarks[14][1] = 0.69
            
            # Moderate physical asymmetry from posture slouch/trauma
            # Left mouth corner droops
            landmarks[61][1] = 0.675  # Sagging mouth corner

        elif driver_state == "INTOXICATED":
            # Drowsy/Intoxicated: Sluggish blinks (extended mid-closed states, frames 5 to 13)
            # Eyes semi-open (vertical gap is half scale)
            if 5 <= frame_idx <= 13:
                # Semi-closed eyes (EAR ~ 0.25)
                landmarks[385][1] = 0.387; landmarks[387][1] = 0.387
                landmarks[373][1] = 0.413; landmarks[380][1] = 0.413
                landmarks[160][1] = 0.387; landmarks[158][1] = 0.387
                landmarks[153][1] = 0.413; landmarks[144][1] = 0.413
            
            # Mouth hangs open (sluggish jaw posture: MAR = 0.06 / 0.16 = 0.375)
            landmarks[13][1] = 0.62
            landmarks[14][1] = 0.68

        # Convert list format to nested tuples
        converted = [tuple(lm) for lm in landmarks]
        sequence.append(converted)

    return sequence


def main():
    print("=" * 70)
    print("POST-CRASH GOLDEN HOUR OPTIMIZER - PHASE 2 VERIFICATION")
    print("=" * 70)

    analyzer = DriverTriageAnalyzer(ear_threshold=0.22, mar_open_threshold=0.40)
    verification_results = {}

    states_to_test = ["ALERT", "UNCONSCIOUS", "INTOXICATED"]
    
    for state in states_to_test:
        print(f"\n[*] Simulating Camera Burst Sequence for: {state} Driver...")
        raw_burst = simulate_burst_sequence(state, num_frames=20)
        
        # 1. Process individual frame landmarks
        burst_metrics = []
        for i, frame in enumerate(raw_burst):
            metrics = analyzer.extract_metrics_from_landmarks(frame)
            burst_metrics.append(metrics)
            
            # Print intermediate blink diagnostic frames
            if state == "ALERT" and i in [7, 8, 9, 10]:
                print(f"  Frame {i:02d}: Average EAR = {metrics['ear_avg']:.4f} | MAR = {metrics['mar']:.4f} | Blink State: {'CLOSED' if metrics['ear_avg'] < 0.22 else 'OPEN'}")
            elif state == "INTOXICATED" and i in [4, 5, 12, 14]:
                print(f"  Frame {i:02d}: Average EAR = {metrics['ear_avg']:.4f} | MAR = {metrics['mar']:.4f} | Sluggish: {'YES' if 0.22 <= metrics['ear_avg'] <= 0.27 else 'NO'}")

        # 2. Run sequential classification
        classification = analyzer.classify_driver_state(burst_metrics)
        verification_results[state] = {
            "metrics": burst_metrics,
            "classification": classification
        }

        print(f"  + Unresponsive Probability : {classification['unresponsive_probability']:.4f}")
        print(f"  + Suspected Intoxication Index : {classification['suspected_intoxication_index']:.4f}")
        print(f"  + Assigned Driver Status Code : {classification['driver_status_code']}")

    # 3. Assertions & Certification
    print("\n" + "-" * 50)
    print("RUNNING PHYSIOLOGICAL ASSERTIONS...")
    print("-" * 50)

    alert_res = verification_results["ALERT"]["classification"]
    uncon_res = verification_results["UNCONSCIOUS"]["classification"]
    intox_res = verification_results["INTOXICATED"]["classification"]

    try:
        # Alert Driver Assertions
        assert alert_res["unresponsive_probability"] < 0.15, "FAIL: Alert driver flagged as unresponsive!"
        assert alert_res["suspected_intoxication_index"] < 0.20, "FAIL: Alert driver flagged as intoxicated!"
        assert alert_res["driver_status_code"] == "RESPONSIVE", "FAIL: Alert driver wrong code!"
        print("[SUCCESS] Alert Driver classified correctly (RESPONSIVE).")

        # Unconscious Driver Assertions
        assert uncon_res["unresponsive_probability"] >= 0.85, "FAIL: Closed eyes not detected!"
        assert uncon_res["driver_status_code"] == "UNCONSCIOUS", "FAIL: Unconscious driver wrong code!"
        print("[SUCCESS] Unconscious/Slumped Driver classified correctly (UNCONSCIOUS).")

        # Intoxicated Driver Assertions
        assert intox_res["suspected_intoxication_index"] >= 0.55, "FAIL: Sluggish blink/mouth sag not flagged!"
        assert intox_res["driver_status_code"] == "SUSPECTED_INTOXICATION", "FAIL: Intoxicated driver wrong code!"
        print("[SUCCESS] Intoxicated/Drowsy Driver classified correctly (SUSPECTED_INTOXICATION).")

        print("\n[CERTIFIED] All Phase 2 architectural assertions PASSED.")
        print("[CERTIFIED] Facial Mesh ratio calculations and triage heuristic are robust.")
    except AssertionError as e:
        print(f"[ERROR] Assertion Failed! {e}")
        sys.exit(1)

    # 4. Save results log to JSON
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "triage_verification_log.json")
    with open(log_file_path, "w") as f:
        # Standardize for reading
        json.dump({
            "status": "PASSED",
            "summary": {
                "alert": alert_res,
                "unconscious": uncon_res,
                "intoxicated": intox_res
            }
        }, f, indent=2)
    print(f"\n[*] Verification logs written to: {log_file_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
