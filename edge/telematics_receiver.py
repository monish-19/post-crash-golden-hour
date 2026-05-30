"""
Post-Crash Golden Hour Optimizer
Phase ①: Auto-Detect & Anti-Gravity Filter (0-10 Seconds)

This module implements the core anti-gravity low-pass filter to isolate true linear
acceleration vectors from raw mobile/vehicle telematics streams. It tracks the
gravity vector dynamically and subtracts it to isolate true, external G-Forces,
enabling robust crash detection with zero false-positives under standard driving behavior.
"""

import math
from typing import Dict, Any, Optional, Tuple


class TelematicsReceiver:
    """
    Handles high-frequency vehicle telematics data, applies an anti-gravity filter,
    calculates isolated G-Forces, and determines crash predictions.
    """

    def __init__(self, lpf_alpha: float = 0.95, speed_window_seconds: float = 1.0):
        """
        Initializes the telematics receiver.

        Args:
            lpf_alpha (float): Low-pass filter constant (alpha) for gravity tracking.
                               Close to 1.0 filters out high frequency changes (standard gravity tracking).
                               Close to 0.0 tracks raw acceleration changes quickly.
            speed_window_seconds (float): Window size in seconds to check speed deceleration.
        """
        self.lpf_alpha = lpf_alpha
        self.speed_window_seconds = speed_window_seconds

        # State tracking variables
        self.gravity_x: Optional[float] = None
        self.gravity_y: Optional[float] = None
        self.gravity_z: Optional[float] = None

        # Ring-buffer/history of telematics to calculate speed deceleration delta over time
        # Contains tuples of (timestamp_seconds, speed_kmph)
        self.telemetry_history = []

    def reset(self):
        """Resets the state of the receiver (e.g., between runs)."""
        self.gravity_x = None
        self.gravity_y = None
        self.gravity_z = None
        self.telemetry_history.clear()

    def process_reading(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a single high-frequency telematics reading.

        Expected schema for 'data':
        {
            "timestamp": float,      # Epoch timestamp or elapsed seconds
            "latitude": float,
            "longitude": float,
            "speed_kmph": float,
            "accel_x": float,        # raw accelerometer X (m/s^2)
            "accel_y": float,        # raw accelerometer Y (m/s^2)
            "accel_z": float         # raw accelerometer Z (m/s^2)
        }

        Returns:
            Dict[str, Any]: Enrichment payload containing raw and computed metrics.
        """
        # Extract inputs
        t = float(data["timestamp"])
        lat = float(data["latitude"])
        lon = float(data["longitude"])
        speed = float(data["speed_kmph"])
        ax = float(data["accel_x"])
        ay = float(data["accel_y"])
        az = float(data["accel_z"])

        # Update telemetry history
        self.telemetry_history.append((t, speed))
        
        # Prune telemetry history to keep only readings within our lookback window
        cutoff_time = t - self.speed_window_seconds
        self.telemetry_history = [
            record for record in self.telemetry_history if record[0] >= cutoff_time
        ]

        # Calculate severe deceleration delta
        # Deceleration delta = speed_current - speed_start_of_window
        # Negative delta indicates deceleration (speed decrease)
        if len(self.telemetry_history) > 1:
            deceleration_delta = speed - self.telemetry_history[0][1]
        else:
            deceleration_delta = 0.0

        # Initialize gravity vector if not yet established
        if self.gravity_x is None:
            self.gravity_x = ax
            self.gravity_y = ay
            self.gravity_z = az
        else:
            # Apply low-pass filter to raw accelerations to track slow-moving gravity vector
            self.gravity_x = self.lpf_alpha * self.gravity_x + (1 - self.lpf_alpha) * ax
            self.gravity_y = self.lpf_alpha * self.gravity_y + (1 - self.lpf_alpha) * ay
            self.gravity_z = self.lpf_alpha * self.gravity_z + (1 - self.lpf_alpha) * az

        # Apply Anti-Gravity physics filter to calculate linear acceleration vectors
        linear_x = ax - self.gravity_x
        linear_y = ay - self.gravity_y
        linear_z = az - self.gravity_z

        # Compute total linear acceleration magnitude (Euclidean norm)
        total_magnitude = math.sqrt(linear_x**2 + linear_y**2 + linear_z**2)

        # Isolate G-force (ratio of magnitude to standard Earth gravity constant g = 9.81)
        isolated_g_force = total_magnitude / 9.81

        # Crash Flag Trigger Logic
        # Set predicted_accident = 1 if Isolated G-Force exceeds 4.0 G
        # simultaneously with a severe deceleration delta (e.g. speed drop of 15 km/h or more in the window)
        is_high_g = isolated_g_force > 4.0
        is_severe_deceleration = deceleration_delta <= -15.0  # Speed dropped by at least 15 km/h

        predicted_accident = 1 if (is_high_g and is_severe_deceleration) else 0

        # Build output dictionary matching the system specifications
        payload = {
            "timestamp": t,
            "latitude": lat,
            "longitude": lon,
            "speed_kmph": speed,
            "accel_x": ax,
            "accel_y": ay,
            "accel_z": az,
            "gravity_vector": {
                "x": round(self.gravity_x, 4),
                "y": round(self.gravity_y, 4),
                "z": round(self.gravity_z, 4)
            },
            "linear_accel": {
                "x": round(linear_x, 4),
                "y": round(linear_y, 4),
                "z": round(linear_z, 4)
            },
            "linear_magnitude_mps2": round(total_magnitude, 4),
            "isolated_g_force": round(isolated_g_force, 4),
            "deceleration_delta_kmph": round(deceleration_delta, 4),
            "predicted_accident": predicted_accident
        }

        return payload
