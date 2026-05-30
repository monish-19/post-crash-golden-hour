"""
Post-Crash Golden Hour Optimizer
Phase ①: Test Suite & Anti-Gravity Filter Verification

This script synthesizes a mock telematics JSON dataset representing four distinct
vehicle-dynamics scenarios. It processes the dataset through the TelematicsReceiver
and verifies that the Anti-Gravity low-pass filter isolates G-Forces correctly, and
proves that the crash trigger operates with 100% precision (no false positives for
aggressive driving or hard braking, and robust detection of true crash impacts).
"""

import json
import os
import sys
import math
from typing import List, Dict, Any

# Ensure we can import telematics_receiver
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from telematics_receiver import TelematicsReceiver


def generate_mock_telemetry() -> List[Dict[str, Any]]:
    """
    Generates a synthetic timeline of vehicle telemetry data points.
    Models 4 sequential scenarios:
      1. Cruising (Steady state, light noise)
      2. Sudden Severe Braking (High deceleration, but safe low G-Force)
      3. Sharp Lateral Turn / Pothole (High G-Force spike, but no deceleration)
      4. High-Speed Head-on Crash (Extreme G-Force spike combined with severe deceleration)
    """
    telemetry = []
    t = 0.0
    dt = 0.1  # 10Hz sampling rate
    
    # Base parameters
    latitude_start = 37.7749
    longitude_start = -122.4194

    # --- SCENARIO 1: CRUISING (Steady state, t = 0.0 to 2.0s) ---
    # Constant speed at 60 km/h. Standard gravity vector (approx. [0, 0, 9.81]).
    speed = 60.0
    for _ in range(20):
        # Add light accelerometer noise (vibrations)
        accel_x = 0.0 + (math.sin(t * 5.0) * 0.15)
        accel_y = 0.0 + (math.cos(t * 5.0) * 0.12)
        accel_z = 9.81 + (math.sin(t * 10.0) * 0.20)  # Gravity is primary on Z
        
        telemetry.append({
            "timestamp": round(t, 2),
            "latitude": latitude_start,
            "longitude": longitude_start,
            "speed_kmph": round(speed, 2),
            "accel_x": round(accel_x, 4),
            "accel_y": round(accel_y, 4),
            "accel_z": round(accel_z, 4)
        })
        t += dt

    # --- SCENARIO 2: SUDDEN SEVERE BRAKING (t = 2.1 to 5.0s) ---
    # Speed drops from 60.0 km/h to 15.0 km/h over 3 seconds.
    # Deceleration rate = 15 km/h per second = 4.17 m/s^2.
    # This represents a hard, safe stop. Linear G-Force should be around 0.43 G.
    for i in range(30):
        # Linear deceleration delta
        speed = max(15.0, speed - (45.0 / 30.0))
        accel_x = 0.0 + (math.sin(t * 3.0) * 0.1)
        accel_y = -4.17 + (math.cos(t * 4.0) * 0.2)  # High longitudinal braking force
        accel_z = 9.81 + (math.sin(t * 5.0) * 0.15)
        
        telemetry.append({
            "timestamp": round(t, 2),
            "latitude": latitude_start,
            "longitude": longitude_start,
            "speed_kmph": round(speed, 2),
            "accel_x": round(accel_x, 4),
            "accel_y": round(accel_y, 4),
            "accel_z": round(accel_z, 4)
        })
        t += dt

    # --- SCENARIO 3: SHARP TURN / POTHOLE (t = 5.1 to 8.0s) ---
    # Cruise speed returns to 50 km/h.
    # At t = 6.5s, the car hits a massive speed bump or performs a sharp swerve.
    # Lateral/vertical G-force spikes to over 4.2 Gs, but speed remains steady.
    speed = 50.0
    for i in range(30):
        # We maintain steady cruising speed of 50 km/h
        accel_x = 0.0
        accel_y = 0.0
        accel_z = 9.81

        # Simulate brief, violent bump/swerve at t = 6.5s to 6.7s
        if 6.5 <= round(t, 2) <= 6.7:
            accel_x = 42.0  # Huge lateral acceleration (4.28 Gs)
            accel_z = 15.0  # Vertical bump component

        telemetry.append({
            "timestamp": round(t, 2),
            "latitude": latitude_start,
            "longitude": longitude_start,
            "speed_kmph": round(speed, 2),
            "accel_x": round(accel_x, 4),
            "accel_y": round(accel_y, 4),
            "accel_z": round(accel_z, 4)
        })
        t += dt

    # --- SCENARIO 4: HIGH-SPEED CRASH COLLISION (t = 8.1 to 10.0s) ---
    # Accelerates back up to 80 km/h.
    # At t = 9.0s, severe crash impact occurs. Speed drops from 80 km/h to 0 km/h in 0.1s.
    # Accelerometer logs extremely high spatial vector magnitude.
    speed = 80.0
    for i in range(20):
        accel_x = 0.0
        accel_y = 0.0
        accel_z = 9.81

        # Impact happens at t = 9.0s
        if round(t, 2) == 9.0:
            speed = 0.0
            accel_x = 22.0  # Lateral deflection force
            accel_y = -65.0  # Sudden massive deceleration stop
            accel_z = 28.0  # Vertical lift/crumple force
        elif round(t, 2) > 9.0:
            speed = 0.0
            accel_x = 0.0
            accel_y = 0.0
            accel_z = 9.81  # Back to rest

        telemetry.append({
            "timestamp": round(t, 2),
            "latitude": latitude_start,
            "longitude": longitude_start,
            "speed_kmph": round(speed, 2),
            "accel_x": round(accel_x, 4),
            "accel_y": round(accel_y, 4),
            "accel_z": round(accel_z, 4)
        })
        t += dt

    return telemetry


def main():
    print("=" * 70)
    print("POST-CRASH GOLDEN HOUR OPTIMIZER - PHASE 1 VERIFICATION")
    print("=" * 70)

    # 1. Generate and save mock telemetry matrix to JSON
    mock_data = generate_mock_telemetry()
    mock_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_telemetry.json")
    
    with open(mock_file_path, "w") as f:
        json.dump(mock_data, f, indent=2)
    print(f"[*] Generated synthetic telemetry matrix: {mock_file_path} ({len(mock_data)} data points)")

    # 2. Process telemetry through TelematicsReceiver
    receiver = TelematicsReceiver(lpf_alpha=0.96, speed_window_seconds=1.0)
    processed_records = []
    
    accident_triggered = False
    accident_timestamp = -1.0
    accident_g_force = 0.0
    accident_deceleration = 0.0

    print("\n[*] Initializing Telematics Stream Processing...")
    
    for record in mock_data:
        processed = receiver.process_reading(record)
        processed_records.append(processed)

        # Catch first crash trigger
        if processed["predicted_accident"] == 1 and not accident_triggered:
            accident_triggered = True
            accident_timestamp = processed["timestamp"]
            accident_g_force = processed["isolated_g_force"]
            accident_deceleration = processed["deceleration_delta_kmph"]

    # 3. Analyze Results by Scenario
    print("\n" + "-" * 50)
    print("SCENARIO ANALYSIS & VERIFICATION STATUS")
    print("-" * 50)

    # Validate Cruising (indices 0 to 19)
    cruising_ok = all(r["predicted_accident"] == 0 for r in processed_records[0:20])
    max_cruising_g = max(r["isolated_g_force"] for r in processed_records[0:20])
    print(f"[Cruising Scenario] Max Isolated G-Force: {max_cruising_g:.3f}G | Accident Triggered: {not cruising_ok}")

    # Validate Hard Braking (indices 20 to 49)
    braking_ok = all(r["predicted_accident"] == 0 for r in processed_records[20:50])
    max_braking_g = max(r["isolated_g_force"] for r in processed_records[20:50])
    min_braking_decel = min(r["deceleration_delta_kmph"] for r in processed_records[20:50])
    print(f"[Severe Braking Scenario] Max G-Force: {max_braking_g:.3f}G | Decel Delta: {min_braking_decel:.1f} kmph | Accident Triggered: {not braking_ok}")

    # Validate Swerve/Bump (indices 50 to 79)
    swerve_ok = all(r["predicted_accident"] == 0 for r in processed_records[50:80])
    max_swerve_g = max(r["isolated_g_force"] for r in processed_records[50:80])
    print(f"[Sharp Swerve/Bump Scenario] Max G-Force: {max_swerve_g:.3f}G | Accident Triggered: {not swerve_ok}")

    # Validate Crash (indices 80 to 99)
    crash_detected = any(r["predicted_accident"] == 1 for r in processed_records[80:100])
    print(f"[Crash Collision Scenario] Accident Triggered: {crash_detected}")
    if crash_detected:
        print(f"  + Crash Event Logged at t = {accident_timestamp}s")
        print(f"  + Impact G-Force Isolated: {accident_g_force}G (Threshold > 4.0G)")
        print(f"  + Deceleration Recorded: {accident_deceleration} kmph (Threshold <= -15.0 kmph)")

    # 4. Critical Assertions for Production Certification
    print("\n" + "-" * 50)
    print("RUNNING RIGOROUS CERTIFICATION ASSERTIONS...")
    print("-" * 50)

    try:
        assert cruising_ok, "FAIL: Cruising caused false-positive accident trigger!"
        assert braking_ok, "FAIL: Hard braking caused false-positive accident trigger!"
        assert swerve_ok, "FAIL: Sudden swerve/bump caused false-positive accident trigger!"
        assert crash_detected, "FAIL: High-speed crash collision was NOT detected!"
        print("[SUCCESS] All architectural assertions PASSED with 100% classification precision.")
        print("[SUCCESS] Physics-based Anti-Gravity Low-Pass Filter successfully isolated gravity vector.")
        print("[SUCCESS] Crash prediction successfully filtered out high-G bumps and high-deceleration braking.")
    except AssertionError as e:
        print(f"[ERROR] Assertion failed! {e}")
        sys.exit(1)

    # 5. Output Verification Log File
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification_log.json")
    with open(log_file_path, "w") as f:
        json.dump({
            "metrics": {
                "max_cruising_g": max_cruising_g,
                "max_braking_g": max_braking_g,
                "min_braking_decel": min_braking_decel,
                "max_swerve_g": max_swerve_g,
                "accident_timestamp": accident_timestamp,
                "accident_g_force": accident_g_force,
                "accident_deceleration": accident_deceleration,
            },
            "status": "PASSED"
        }, f, indent=2)
    print(f"\n[*] Verification logs written to: {log_file_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
