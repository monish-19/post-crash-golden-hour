"""
Post-Crash Golden Hour Optimizer
Phase ②: Driver Triage & Sobriety Analysis (10-30 Seconds)

This module integrates MediaPipe Face Mesh geometry analysis to assess driver responsiveness
and suspected intoxication levels following a severe vehicle crash. It computes:
  1. Eye Aspect Ratio (EAR) to detect responsive blinking vs. closed/unconscious eyes.
  2. Mouth Aspect Ratio (MAR) to detect facial sagging or slackness from impact/trauma.
  3. Facial Asymmetry Index to evaluate physical sagging or facial trauma.
  4. Probabilistic classification matrices for driver unresponsiveness and intoxication.
"""

import json
import math
import os
from typing import List, Dict, Any, Tuple, Optional

# Standard scientific modules (pre-verified and installed)
import numpy as np

# MediaPipe is imported within a try-block to ensure headless environments can load
# the script without errors even if raw X11/display drivers are missing.
try:
    import cv2
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


class DriverTriageAnalyzer:
    """
    Analyzes driver face geometry coordinates using MediaPipe Face Mesh to determine
    medical unresponsiveness and sobriety status following a crash collision.
    """

    # Face Mesh Indices Mapping (Ref: MediaPipe Landmark Canonical Map)
    LEFT_EYE_INDICES = {
        "p1": 362,  # Horizontal Left Corner
        "p2": 385,  # Upper vertical 1
        "p3": 387,  # Upper vertical 2
        "p4": 263,  # Horizontal Right Corner
        "p5": 373,  # Lower vertical 2
        "p6": 380   # Lower vertical 1
    }

    RIGHT_EYE_INDICES = {
        "p1": 33,   # Horizontal Left Corner
        "p2": 160,  # Upper vertical 1
        "p3": 158,  # Upper vertical 2
        "p4": 133,  # Horizontal Right Corner
        "p5": 153,  # Lower vertical 2
        "p6": 144   # Lower vertical 1
    }

    MOUTH_INDICES = {
        "left": 61,
        "right": 291,
        "upper": 13,
        "lower": 14
    }

    # Symmetrical pairs for facial asymmetry assessment
    ASYMMETRY_PAIRS = [
        (70, 300),   # Outer left eyebrow vs Outer right eyebrow
        (234, 454),  # Left outer cheek cheekbone vs Right outer cheek cheekbone
        (61, 291)    # Left mouth corner vs Right mouth corner
    ]

    def __init__(self, ear_threshold: float = 0.22, mar_open_threshold: float = 0.40):
        """
        Initializes the Driver Triage Analyzer.

        Args:
            ear_threshold (float): EAR value below which eyes are classified as closed.
            mar_open_threshold (float): MAR value above which mouth is classified as sagging/open.
        """
        self.ear_threshold = ear_threshold
        self.mar_open_threshold = mar_open_threshold

        # Initialize MediaPipe if available
        self.mp_face_mesh = None
        self.face_mesh_detector = None
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh_detector = self.mp_face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            except Exception as e:
                print(f"[!] MediaPipe initialization failed: {e}. Falling back to coordinate mode.")

    @staticmethod
    def _euclidean_distance(pt1: Tuple[float, float, float], pt2: Tuple[float, float, float]) -> float:
        """Computes the 3D Euclidean distance between two coordinate tuples."""
        return math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2 + (pt1[2] - pt2[2])**2)

    def calculate_ear(self, landmarks: List[Tuple[float, float, float]], eye_mapping: Dict[str, int]) -> float:
        """
        Calculates the Eye Aspect Ratio (EAR) for a single eye.
        Formula: EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
        """
        p1 = landmarks[eye_mapping["p1"]]
        p2 = landmarks[eye_mapping["p2"]]
        p3 = landmarks[eye_mapping["p3"]]
        p4 = landmarks[eye_mapping["p4"]]
        p5 = landmarks[eye_mapping["p5"]]
        p6 = landmarks[eye_mapping["p6"]]

        d_vert1 = self._euclidean_distance(p2, p6)
        d_vert2 = self._euclidean_distance(p3, p5)
        d_horiz = self._euclidean_distance(p1, p4)

        if d_horiz == 0.0:
            return 0.0
        return (d_vert1 + d_vert2) / (2.0 * d_horiz)

    def calculate_mar(self, landmarks: List[Tuple[float, float, float]]) -> float:
        """
        Calculates the Mouth Aspect Ratio (MAR) to evaluate jaw slackness/openness.
        Formula: MAR = ||upper - lower|| / ||left - right||
        """
        m_left = landmarks[self.MOUTH_INDICES["left"]]
        m_right = landmarks[self.MOUTH_INDICES["right"]]
        m_upper = landmarks[self.MOUTH_INDICES["upper"]]
        m_lower = landmarks[self.MOUTH_INDICES["lower"]]

        d_vert = self._euclidean_distance(m_upper, m_lower)
        d_horiz = self._euclidean_distance(m_left, m_right)

        if d_horiz == 0.0:
            return 0.0
        return d_vert / d_horiz

    def calculate_facial_asymmetry(self, landmarks: List[Tuple[float, float, float]]) -> float:
        """
        Calculates a relative index of left-right vertical facial asymmetry to detect half-face sagging.
        Measures vertical height delta between symmetrical outer-face nodes relative to head width.
        """
        # Symmetrical width benchmark: distance between outer cheeks (index 234 and 454)
        cheek_left = landmarks[234]
        cheek_right = landmarks[454]
        face_width = self._euclidean_distance(cheek_left, cheek_right)
        
        if face_width == 0.0:
            return 0.0

        vertical_deltas = []
        for left_idx, right_idx in self.ASYMMETRY_PAIRS:
            y_left = landmarks[left_idx][1]
            y_right = landmarks[right_idx][1]
            vertical_deltas.append(abs(y_left - y_right))
            
        # Normalize relative to total face scale
        return sum(vertical_deltas) / face_width

    def extract_metrics_from_landmarks(self, landmarks: List[Tuple[float, float, float]]) -> Dict[str, float]:
        """
        Processes standard extracted coordinates to return core eye and mouth dynamic aspects.
        """
        ear_left = self.calculate_ear(landmarks, self.LEFT_EYE_INDICES)
        ear_right = self.calculate_ear(landmarks, self.RIGHT_EYE_INDICES)
        ear_avg = (ear_left + ear_right) / 2.0
        mar = self.calculate_mar(landmarks)
        asymmetry = self.calculate_facial_asymmetry(landmarks)

        return {
            "ear_left": round(ear_left, 4),
            "ear_right": round(ear_right, 4),
            "ear_avg": round(ear_avg, 4),
            "mar": round(mar, 4),
            "facial_asymmetry_index": round(asymmetry, 4)
        }

    def process_image(self, image_np: np.ndarray) -> Optional[Dict[str, float]]:
        """
        Processes a raw image frame using MediaPipe Face Mesh, returning extracted eye/mouth metrics.
        Returns None if no face is detected.
        """
        if not MEDIAPIPE_AVAILABLE or self.face_mesh_detector is None:
            return None

        # Convert to RGB as expected by MediaPipe
        rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        results = self.face_mesh_detector.process(rgb_image)

        if not results.multi_face_landmarks:
            return None

        # Take first detected face
        face_landmarks = results.multi_face_landmarks[0]
        
        # Convert landmarks to List[Tuple[x, y, z]]
        coordinates = []
        for lm in face_landmarks.landmark:
            coordinates.append((lm.x, lm.y, lm.z))

        return self.extract_metrics_from_landmarks(coordinates)

    def classify_driver_state(self, burst_history: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Processes a sequential history dictionary (representing a camera burst window)
        to evaluate unresponsive_probability and suspected_intoxication_index.
        """
        if not burst_history:
            return {
                "unresponsive_probability": 0.0,
                "suspected_intoxication_index": 0.0,
                "driver_status_code": "UNKNOWN"
            }

        total_frames = len(burst_history)
        
        # 1. Evaluate Unconsciousness/Unresponsiveness
        # Unresponsive driver maintains eyes closed (EAR < 0.22) sustained across the burst
        closed_frames = sum(1 for f in burst_history if f["ear_avg"] < self.ear_threshold)
        unresponsive_prob = closed_frames / total_frames

        # 2. Evaluate Suspected Intoxication
        # Drowsy/Intoxicated driver features sluggish blinks (prolonged intermediate states: EAR ~ 0.22-0.27)
        # Combined with jaw/mouth sagging (MAR ~ 0.28-0.45) or elevated facial asymmetry.
        sluggish_blink_frames = sum(
            1 for f in burst_history 
            if self.ear_threshold <= f["ear_avg"] <= 0.27
        )
        sluggish_blink_factor = sluggish_blink_frames / total_frames

        mouth_sag_frames = sum(
            1 for f in burst_history 
            if 0.28 <= f["mar"] <= 0.45
        )
        mouth_sag_factor = mouth_sag_frames / total_frames

        avg_asymmetry = np.mean([f["facial_asymmetry_index"] for f in burst_history])
        asymmetry_factor = min(1.0, avg_asymmetry / 0.08)  # Scaled asymmetry factor

        # Intoxication Index formula using weighted physiological heuristics
        suspected_intox_idx = (
            0.45 * sluggish_blink_factor + 
            0.40 * mouth_sag_factor + 
            0.15 * asymmetry_factor
        )
        # Clip to ensure range limit bounds [0.0, 1.0]
        suspected_intox_idx = max(0.0, min(1.0, suspected_intox_idx))

        # Assign status code
        if unresponsive_prob >= 0.75:
            status_code = "UNCONSCIOUS"
        elif suspected_intox_idx >= 0.55:
            status_code = "SUSPECTED_INTOXICATION"
        else:
            status_code = "RESPONSIVE"

        return {
            "unresponsive_probability": round(unresponsive_prob, 4),
            "suspected_intoxication_index": round(suspected_intox_idx, 4),
            "driver_status_code": status_code
        }
