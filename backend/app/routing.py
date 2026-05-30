"""
Post-Crash Golden Hour Optimizer
Phase ③: Route Optimization & Green-Corridor Dispatch (30-45 Seconds)

This module implements the backend routing engine. It parses active city hospital
ER bed metrics and trauma levels, applies a multi-factor scoring optimization algorithm,
simulates Mapbox dynamic traffic congestion matrices, and generates predictive traffic light
preemption command streams ("Green Corridors") for upcoming emergency path junctions.
"""

import json
import math
import os
from typing import List, Dict, Any, Tuple

# Constants
EARTH_RADIUS_KM = 6371.0


class RouteOptimizer:
    """
    Optimizes emergency route dispatching by combining patient medical priority,
    geospatial Haversine distances, real-time traffic speeds, and hospital ER capacity.
    """

    def __init__(self, hospitals_json_path: str):
        """Initializes the Route Optimizer by loading the hospital database."""
        self.hospitals_json_path = hospitals_json_path
        self.hospitals = self.load_hospitals()

    def load_hospitals(self) -> List[Dict[str, Any]]:
        """Loads hospital profiles from the database."""
        if not os.path.exists(self.hospitals_json_path):
            raise FileNotFoundError(f"Hospital database not found at: {self.hospitals_json_path}")
        with open(self.hospitals_json_path, "r") as f:
            return json.load(f)

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates the great-circle distance between two points on the Earth's surface
        using the Haversine formula.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

        return EARTH_RADIUS_KM * c

    def calculate_traffic_eta(self, hospital: Dict[str, Any], crash_lat: float, crash_lon: float) -> Tuple[float, float]:
        """
        Simulates Mapbox routing matrix with traffic factors.
        Mercy General and Metro Trauma use high-speed highway routes (base speed 80 km/h).
        City Memorial and Valley Community use surface streets (base speed 45 km/h).
        
        Returns:
            Tuple[float, float]: (distance_km, eta_minutes)
        """
        dist_km = self.haversine_distance(crash_lat, crash_lon, hospital["latitude"], hospital["longitude"])

        # Determine route speed limit and congestion index
        # Mercy: moderate traffic (1.2)
        # City Memorial: light traffic (1.1)
        # Valley Community: smooth flow (1.0)
        # Metro Trauma: extreme gridlock / accident delay (2.2)
        hosp_id = hospital["id"]
        if hosp_id == "hosp_mercy_general":
            base_speed = 80.0
            traffic_factor = 1.2
        elif hosp_id == "hosp_metro_trauma":
            base_speed = 80.0
            traffic_factor = 2.2  # Severe congestion block!
        elif hosp_id == "hosp_city_memorial":
            base_speed = 45.0
            traffic_factor = 1.1
        else:  # Valley Clinic
            base_speed = 45.0
            traffic_factor = 1.0

        # Calculate time: time = (distance / speed) * traffic_factor * 60 minutes
        base_time_hours = dist_km / base_speed
        eta_minutes = base_time_hours * traffic_factor * 60.0

        # Ensure a minimum travel time (e.g. 1.5 minutes for short distances)
        eta_minutes = max(1.5, eta_minutes)

        return round(dist_km, 3), round(eta_minutes, 2)

    def select_optimal_hospital(self, crash_lat: float, crash_lon: float, driver_status_code: str) -> Dict[str, Any]:
        """
        Applies the multi-factor weighted scoring matrix to choose the optimal hospital.
        
        Scoring Formulas:
          Score = w_eta * ETA_Score + w_beds * Bed_Score + w_trauma * Trauma_Score
        """
        scored_hospitals = []

        for hosp in self.hospitals:
            dist_km, eta_min = self.calculate_traffic_eta(hosp, crash_lat, crash_lon)

            # 1. Compute ETA Score (0 to 100, where higher is faster/better)
            # Benchmark: 20 minutes is 0, 0 minutes is 100
            eta_score = max(0.0, min(100.0, 100.0 - (eta_min * 5.0)))

            # 2. Compute Bed Availability Score (0 to 100)
            avail_beds = hosp["available_er_beds"]
            if avail_beds == 0:
                bed_score = 0.0  # Completely full!
            elif avail_beds > 5:
                bed_score = 100.0
            else:
                bed_score = 50.0 + (avail_beds * 8.0)  # Moderate constraint

            # 3. Compute Trauma Level Match Score (0 to 100)
            t_level = hosp["trauma_level"]
            if driver_status_code == "UNCONSCIOUS":
                # Critical driver needs Level 1 immediately
                if t_level == 1:
                    trauma_score = 100.0
                elif t_level == 2:
                    trauma_score = 50.0
                else:
                    trauma_score = 10.0
            else:
                # Responsive/Sober/Intoxicated driver should prioritize Level 2/3
                # to save Level 1 bays for absolute extreme cases.
                if t_level == 2:
                    trauma_score = 100.0
                elif t_level == 3:
                    trauma_score = 80.0
                else:
                    trauma_score = 50.0  # Discourage using Level 1 for stable victims

            # 4. Compute Final Weighted Score based on patient urgency
            if driver_status_code == "UNCONSCIOUS":
                # High priority to Trauma level and fast travel time
                w_trauma = 0.45
                w_eta = 0.40
                w_bed = 0.15
            else:
                # Normal priority, saving high-trauma bays. Bed availability is key.
                w_trauma = 0.20
                w_eta = 0.30
                w_bed = 0.50

            total_score = (w_trauma * trauma_score) + (w_eta * eta_score) + (w_bed * bed_score)

            scored_hospitals.append({
                "hospital": hosp,
                "distance_km": dist_km,
                "eta_minutes": eta_min,
                "scores": {
                    "trauma": trauma_score,
                    "eta": round(eta_score, 2),
                    "bed": bed_score,
                    "total": round(total_score, 2)
                }
            })

        # Sort scored hospitals by total score descending (highest score is optimal)
        scored_hospitals.sort(key=lambda x: x["scores"]["total"], reverse=True)
        
        # Take the top matched hospital
        best_match = scored_hospitals[0]
        
        # Generate Green Corridor preemption checkpoints along the chosen path
        green_corridor = self.generate_green_corridor(
            crash_lat, crash_lon, 
            best_match["hospital"]["latitude"], best_match["hospital"]["longitude"], 
            best_match["eta_minutes"]
        )

        return {
            "selected_hospital": best_match["hospital"],
            "distance_km": best_match["distance_km"],
            "eta_minutes": best_match["eta_minutes"],
            "dispatch_score": best_match["scores"]["total"],
            "green_corridor_intersections": green_corridor,
            "all_evaluated_options": scored_hospitals
        }

    def generate_green_corridor(self, start_lat: float, start_lon: float, end_lat: float, end_lon: float, eta_minutes: float) -> List[Dict[str, Any]]:
        """
        Places 3 predictive traffic light preemption intersections along the route.
        Calculates exact vehicle arrival windows.
        """
        intersections = []
        eta_seconds = eta_minutes * 60.0
        
        # Names for simulated junctions
        names = ["Junction Alpha (Ring Road)", "Junction Beta (Broadway St)", "Junction Gamma (Trauma Way)"]

        for i in range(3):
            # Fraction along path (25%, 50%, 75%)
            fraction = (i + 1) * 0.25
            
            # Linearly interpolate coordinates
            lat = start_lat + fraction * (end_lat - start_lat)
            lon = start_lon + fraction * (end_lon - start_lon)
            
            # Calculate ETA to intersection
            time_to_intersection_sec = eta_seconds * fraction
            
            # Preemption pre-trigger window (activate 15 seconds before arrival, hold 20 seconds after)
            t_start = max(0.0, time_to_intersection_sec - 15.0)
            t_end = time_to_intersection_sec + 20.0

            intersections.append({
                "intersection_id": f"int_checkpoint_{i+1:02d}",
                "name": names[i],
                "latitude": round(lat, 5),
                "longitude": round(lon, 5),
                "estimated_arrival_seconds": round(time_to_intersection_sec, 1),
                "preemption_window_seconds": [round(t_start, 1), round(t_end, 1)],
                "preemption_status": "PREEMPTING"
            })

        return intersections
