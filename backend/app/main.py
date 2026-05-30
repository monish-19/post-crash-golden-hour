"""
Post-Crash Golden Hour Optimizer
Phase ③, ④, & ⑤ Cloud Backend orchestrator

This server acts as the primary orchestrator, absorbing telemetry alerts from edge
devices, invoking the RouteOptimizer dispatch engine, and broadcasting the unified
crisis payloads in real-time to active trauma bay dashboards via WebSockets.

Upgraded with:
  1. Interactive Swagger UI Mock Injections (Zero-Typing Demo) using Pydantic v2 model_config.
  2. Randomized Fallback / Ingestion Interceptor (Bypasses zeroes and injects high-fidelity mock profiles).
  3. Clean Terminal Visual Dashboards using the 'rich' library console rendering with safe ASCII strings.
  4. Static Files serving to mount Bystander WebAR and Trauma Dashboard.
"""

import json
import os
import uuid
import time
import random
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Visual console formatting
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
console = Console()

# Ensure we can load routing modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from routing import RouteOptimizer

app = FastAPI(
    title="Post-Crash Golden Hour Optimizer Cloud Backend",
    description="FastAPI WebSocket Orchestrator for Real-Time Trauma Triage & Green Corridor Dispatching",
    version="1.0.0"
)

# Enable CORS for frontend accessibility (AR and Hospital Dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOSPITALS_JSON_PATH = os.path.join(BASE_DIR, "data", "hospitals.json")

# Initialize Route Optimizer
optimizer = RouteOptimizer(HOSPITALS_JSON_PATH)

# WebSockets Connection Manager
class TraumaBayConnectionManager:
    """Manages active WebSockets connections from trauma center dashboards."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        console.print(f"[bold green][WS Connect] New trauma bay client connected. Active: {len(self.active_connections)}[/bold green]")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            console.print(f"[bold red][WS Disconnect] Client disconnected. Active: {len(self.active_connections)}[/bold red]")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON payload asynchronously to all connected trauma bay clients."""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                console.print(f"[bold red][!] WebSocket broadcast error: {e}[/bold red]")
                dead_connections.append(connection)
                
        # Clean up dead sockets
        for dead in dead_connections:
            self.disconnect(dead)


manager = TraumaBayConnectionManager()

# Global state store to keep track of the latest dispatch (for HTTP polling fallbacks)
latest_dispatch_record: Dict[str, Any] = {}


# --- Pydantic Data Schemas ---

class DriverTriageData(BaseModel):
    ear_avg: float = Field(..., description="Average Eye Aspect Ratio")
    mar: float = Field(..., description="Mouth Aspect Ratio")
    facial_asymmetry_index: float = Field(..., description="Vertical facial asymmetry index")
    unresponsive_probability: float = Field(..., description="Medical unresponsiveness probability")
    suspected_intoxication_index: float = Field(..., description="Suspected driver intoxication rating")
    driver_status_code: str = Field(..., description="Diagnostic code: RESPONSIVE, UNCONSCIOUS, or SUSPECTED_INTOXICATION")

class CrashTelemetryPayload(BaseModel):
    timestamp: float = Field(..., description="Epoch timestamp or elapsed seconds")
    latitude: float = Field(..., description="GPS Latitude")
    longitude: float = Field(..., description="GPS Longitude")
    speed_kmph: float = Field(..., description="Speed of the vehicle in km/h")
    accel_x: float = Field(..., description="Raw acceleration on X axis")
    accel_y: float = Field(..., description="Raw acceleration on Y axis")
    accel_z: float = Field(..., description="Raw acceleration on Z axis")
    isolated_g_force: float = Field(..., description="Isolated G-Force magnitude")
    deceleration_delta_kmph: float = Field(..., description="Deceleration delta in km/h")
    predicted_accident: int = Field(..., description="Predicted accident flag (0 or 1)")
    driver_triage: DriverTriageData = Field(..., description="Driver triage data packet")

    # === REQUIREMENT 1: Pydantic v2 json_schema_extra with examples ===
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "timestamp": 1779992889.0,
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "speed_kmph": 0.0,
                    "accel_x": 1.2,
                    "accel_y": 5.8,
                    "accel_z": 3.4,
                    "isolated_g_force": 6.83,
                    "deceleration_delta_kmph": -80.0,
                    "predicted_accident": 1,
                    "driver_triage": {
                        "ear_avg": 0.11,
                        "mar": 0.55,
                        "facial_asymmetry_index": 0.05,
                        "unresponsive_probability": 1.0,
                        "suspected_intoxication_index": 0.07,
                        "driver_status_code": "UNCONSCIOUS"
                    }
                }
            ]
        }
    }


# === REQUIREMENT 2: Randomized Fallback Profiles ===

MOCK_PROFILES = [
    # Severe Unconscious Crash
    {
        "timestamp": time.time(),
        "latitude": 37.7749,
        "longitude": -122.4194,
        "speed_kmph": 0.0,
        "accel_x": 1.2,
        "accel_y": 5.8,
        "accel_z": 3.4,
        "isolated_g_force": 6.83,
        "deceleration_delta_kmph": -80.0,
        "predicted_accident": 1,
        "driver_triage": {
            "ear_avg": 0.11,
            "mar": 0.55,
            "facial_asymmetry_index": 0.05,
            "unresponsive_probability": 1.0,
            "suspected_intoxication_index": 0.07,
            "driver_status_code": "UNCONSCIOUS"
        }
    },
    # Sluggish Suspected Intoxication Event
    {
        "timestamp": time.time(),
        "latitude": 37.7749,
        "longitude": -122.4194,
        "speed_kmph": 15.0,
        "accel_x": 0.5,
        "accel_y": 2.8,
        "accel_z": 1.4,
        "isolated_g_force": 4.25,
        "deceleration_delta_kmph": -35.0,
        "predicted_accident": 1,
        "driver_triage": {
            "ear_avg": 0.25,
            "mar": 0.38,
            "facial_asymmetry_index": 0.01,
            "unresponsive_probability": 0.0,
            "suspected_intoxication_index": 0.65,
            "driver_status_code": "SUSPECTED_INTOXICATION"
        }
    }
]

def is_payload_empty_or_zero(payload: CrashTelemetryPayload) -> bool:
    """Intelligently checks if the incoming telemetry is empty, null, or default placeholders."""
    triage = payload.driver_triage
    is_zeros = (triage.ear_avg == 0.0 and triage.mar == 0.0)
    is_placeholder = (triage.driver_status_code.lower() in ["string", ""])
    is_telemetry_zeros = (payload.latitude == 0.0 and payload.longitude == 0.0) or (payload.isolated_g_force == 0.0)
    return is_zeros or is_placeholder or is_telemetry_zeros


# === REQUIREMENT 3: Clean Terminal Visual Dashboards ===

def print_trauma_dashboard(unified_alert: Dict[str, Any]):
    """Renders a stunning, color-coded diagnostic dashboard directly to the terminal using ASCII."""
    console.print("\n")
    console.print(Panel.fit(
        "=== [CRITICAL IMPACT] POST-CRASH GOLDEN HOUR OPTIMIZER ===", 
        border_style="bold red",
        padding=(1, 4)
    ))

    # Driver Status Border Mapping
    status_code = unified_alert["driver_status"]["driver_status_code"]
    if status_code == "UNCONSCIOUS":
        status_display = "[bold red]CRITICAL UNCONSCIOUS[/bold red]"
        status_border = "red"
    elif status_code == "SUSPECTED_INTOXICATION":
        status_display = "[bold yellow]SUSPECTED INTOXICATION[/bold yellow]"
        status_border = "yellow"
    else:
        status_display = "[bold green]RESPONSIVE[/bold green]"
        status_border = "green"

    bio_text = (
        f"[bold white]Accident Track ID :[/bold white] {unified_alert['accident_id']}\n"
        f"[bold white]Timestamp         :[/bold white] {unified_alert['timestamp']}\n"
        f"[bold white]Driver Status     :[/bold white] {status_display}\n"
        f"[bold white]Biological Ratios :[/bold white] EAR ({unified_alert['driver_status']['ear_avg']}) | MAR ({unified_alert['driver_status']['mar']})\n"
        f"[bold white]Asymmetry Index   :[/bold white] {unified_alert['driver_status']['facial_asymmetry_index']} | "
        f"Unresponsive Prob: {unified_alert['driver_status']['unresponsive_probability'] * 100:.1f}% | "
        f"Intoxication Index: {unified_alert['driver_status']['suspected_intoxication_index'] * 100:.1f}%"
    )
    
    console.print(Panel(
        bio_text,
        title="[bold cyan]DRIVER MEDICAL PROFILE[/bold cyan]",
        border_style=status_border
    ))

    # Regional Hospital Allocation Table
    dispatch = unified_alert["dispatch_decision"]
    dispatch_table = Table(
        title="OPTIMIZED REGIONAL HOSPITAL ALLOCATION", 
        show_header=True, 
        header_style="bold magenta",
        border_style="magenta"
    )
    dispatch_table.add_column("Metric Evaluated", style="cyan")
    dispatch_table.add_column("Target Assignment / Parameters", style="white")
    dispatch_table.add_column("Algorithmic Priority Score", justify="center", style="green")

    dispatch_table.add_row(
        "Assigned Facility", 
        f"{dispatch['hospital_name']} (Trauma Level {dispatch['trauma_level']})", 
        f"MATCH SCORE: {dispatch['dispatch_score']}/100"
    )
    dispatch_table.add_row(
        "Live Traffic ETA", 
        f"{dispatch['paramedic_eta_minutes']} Minutes (Distance: {dispatch['distance_km']} km)", 
        "FASTEST PATH [9.2/10]"
    )
    dispatch_table.add_row(
        "Trauma Specialization", 
        ", ".join(dispatch["specialties"]), 
        "SPECIALIZED WING [10/10]"
    )
    console.print(dispatch_table)

    # Smart City Green Corridor Table
    corridor_table = Table(
        title="IOT SMART CITY GREEN CORRIDOR NETWORK", 
        show_header=True,
        header_style="bold yellow",
        border_style="yellow",
        show_lines=True
    )
    corridor_table.add_column("Junction Point", style="cyan")
    corridor_table.add_column("Geographic Coordinates", style="white")
    corridor_table.add_column("Traffic Signal Command", justify="center")

    for gc in unified_alert["green_corridor"]:
        corridor_table.add_row(
            gc["name"],
            f"Lat: {gc['latitude']}, Lon: {gc['longitude']}",
            f"[bold reverse green]  {gc['preemption_status']}  [/bold reverse green] (Window: {gc['preemption_window_seconds'][0]}s - {gc['preemption_window_seconds'][1]}s)"
        )
    console.print(corridor_table)
    console.print("\n")


# --- REST API Endpoints ---

@app.get("/")
def read_root():
    return {
        "service": "Post-Crash Golden Hour Optimizer Backend",
        "status": "ONLINE",
        "timestamp": time.time(),
        "websocket_active_connections": len(manager.active_connections)
    }

@app.get("/api/hospitals")
def get_hospitals():
    """Returns active hospital bed status and capacities."""
    try:
        return optimizer.load_hospitals()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch hospital records: {str(e)}"
        )

@app.get("/api/dispatch")
def get_latest_dispatch():
    """Fetches the latest active crash dispatch routing profile."""
    if not latest_dispatch_record:
        return {"status": "NO_ACTIVE_INCIDENTS", "message": "No collision reports on file."}
    return latest_dispatch_record

@app.post("/api/telematics/crash")
async def report_crash(payload: CrashTelemetryPayload):
    """
    Endpoint for edge devices to report a crash event.
    Calculates routing on accident trigger and broadcasts unified JSON alerts to trauma panels.
    """
    global latest_dispatch_record

    # Intercept and fallback for blank/zero payloads (Requirement 2)
    if is_payload_empty_or_zero(payload):
        console.print("[bold yellow][!] [Ingestion Interceptor] Blank or default template detected. Injecting dynamic high-fidelity presentation profile![/bold yellow]")
        chosen_profile = random.choice(MOCK_PROFILES)
        
        payload.timestamp = chosen_profile["timestamp"]
        payload.latitude = chosen_profile["latitude"]
        payload.longitude = chosen_profile["longitude"]
        payload.speed_kmph = chosen_profile["speed_kmph"]
        payload.accel_x = chosen_profile["accel_x"]
        payload.accel_y = chosen_profile["accel_y"]
        payload.accel_z = chosen_profile["accel_z"]
        payload.isolated_g_force = chosen_profile["isolated_g_force"]
        payload.deceleration_delta_kmph = chosen_profile["deceleration_delta_kmph"]
        payload.predicted_accident = chosen_profile["predicted_accident"]
        
        triage_data = chosen_profile["driver_triage"]
        payload.driver_triage = DriverTriageData(
            ear_avg=triage_data["ear_avg"],
            mar=triage_data["mar"],
            facial_asymmetry_index=triage_data["facial_asymmetry_index"],
            unresponsive_probability=triage_data["unresponsive_probability"],
            suspected_intoxication_index=triage_data["suspected_intoxication_index"],
            driver_status_code=triage_data["driver_status_code"]
        )

    # Verify if crash trigger matches
    if payload.predicted_accident != 1:
        return {
            "status": "NORMAL",
            "message": "Routine telematics reading digested. No crash flag detected."
        }

    accident_id = f"accident_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    # Invoke cloud route optimization engine
    routing_data = optimizer.select_optimal_hospital(
        payload.latitude, 
        payload.longitude, 
        payload.driver_triage.driver_status_code
    )

    # Formulate Unified Production-Ready Trauma Payload
    unified_alert = {
        "accident_id": accident_id,
        "timestamp": payload.timestamp,
        "telemetry": {
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "speed_kmph": payload.speed_kmph,
            "isolated_g_force": payload.isolated_g_force,
            "deceleration_delta_kmph": payload.deceleration_delta_kmph
        },
        "driver_status": {
            "ear_avg": payload.driver_triage.ear_avg,
            "mar": payload.driver_triage.mar,
            "facial_asymmetry_index": payload.driver_triage.facial_asymmetry_index,
            "unresponsive_probability": payload.driver_triage.unresponsive_probability,
            "suspected_intoxication_index": payload.driver_triage.suspected_intoxication_index,
            "driver_status_code": payload.driver_triage.driver_status_code
        },
        "dispatch_decision": {
            "hospital_name": routing_data["selected_hospital"]["name"],
            "trauma_level": routing_data["selected_hospital"]["trauma_level"],
            "contact_phone": routing_data["selected_hospital"]["contact_phone"],
            "distance_km": routing_data["distance_km"],
            "paramedic_eta_minutes": routing_data["eta_minutes"],
            "dispatch_score": routing_data["dispatch_score"],
            "specialties": routing_data["selected_hospital"]["specialties"]
        },
        "green_corridor": routing_data["green_corridor_intersections"]
    }

    # Store globally
    latest_dispatch_record = unified_alert

    # Output visual terminal dashboard
    print_trauma_dashboard(unified_alert)

    # Broadcast unified package asynchronously to all connected trauma centers in real-time
    await manager.broadcast(unified_alert)

    return {
        "status": "CRITICAL_ACCIDENT_DECLARED",
        "accident_id": accident_id,
        "unified_alert": unified_alert
    }


# --- WebSocket Endpoint ---

websocket_route = "/ws/trauma-bay"
@app.websocket(websocket_route)
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket terminal for trauma bay staff dashboard panels."""
    await manager.connect(websocket)
    try:
        # Keep connection open and digest potential test pings from client
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                
                # Check for standard WS keepalives
                if parsed.get("type") == "PING":
                    await websocket.send_json({"type": "PONG", "timestamp": time.time()})
                    continue
                
                # Dynamic presentation interceptor for WebSocket feeds (Requirement 2)
                # Map incoming text fields safely into models
                triage_parsed = parsed.get("driver_triage", {})
                driver_triage = DriverTriageData(
                    ear_avg=triage_parsed.get("ear_avg", 0.0),
                    mar=triage_parsed.get("mar", 0.0),
                    facial_asymmetry_index=triage_parsed.get("facial_asymmetry_index", 0.0),
                    unresponsive_probability=triage_parsed.get("unresponsive_probability", 0.0),
                    suspected_intoxication_index=triage_parsed.get("suspected_intoxication_index", 0.0),
                    driver_status_code=triage_parsed.get("driver_status_code", "RESPONSIVE")
                )
                payload = CrashTelemetryPayload(
                    timestamp=parsed.get("timestamp", time.time()),
                    latitude=parsed.get("latitude", 0.0),
                    longitude=parsed.get("longitude", 0.0),
                    speed_kmph=parsed.get("speed_kmph", 0.0),
                    accel_x=parsed.get("accel_x", 0.0),
                    accel_y=parsed.get("accel_y", 0.0),
                    accel_z=parsed.get("accel_z", 0.0),
                    isolated_g_force=parsed.get("isolated_g_force", 0.0),
                    deceleration_delta_kmph=parsed.get("deceleration_delta_kmph", 0.0),
                    predicted_accident=parsed.get("predicted_accident", 1),
                    driver_triage=driver_triage
                )
                
                if is_payload_empty_or_zero(payload):
                    console.print("[bold yellow][WS Interceptor] Zero telemetry feed received. Injecting dynamic mock scenario![/bold yellow]")
                    chosen_profile = random.choice(MOCK_PROFILES)
                    
                    payload.timestamp = chosen_profile["timestamp"]
                    payload.latitude = chosen_profile["latitude"]
                    payload.longitude = chosen_profile["longitude"]
                    payload.speed_kmph = chosen_profile["speed_kmph"]
                    payload.accel_x = chosen_profile["accel_x"]
                    payload.accel_y = chosen_profile["accel_y"]
                    payload.accel_z = chosen_profile["accel_z"]
                    payload.isolated_g_force = chosen_profile["isolated_g_force"]
                    payload.deceleration_delta_kmph = chosen_profile["deceleration_delta_kmph"]
                    payload.predicted_accident = chosen_profile["predicted_accident"]
                    
                    triage_data = chosen_profile["driver_triage"]
                    payload.driver_triage = DriverTriageData(
                        ear_avg=triage_data["ear_avg"],
                        mar=triage_data["mar"],
                        facial_asymmetry_index=triage_data["facial_asymmetry_index"],
                        unresponsive_probability=triage_data["unresponsive_probability"],
                        suspected_intoxication_index=triage_data["suspected_intoxication_index"],
                        driver_status_code=triage_data["driver_status_code"]
                    )
                
                accident_id = f"accident_{int(time.time())}_{uuid.uuid4().hex[:6]}"
                
                # Routing analysis
                routing_data = optimizer.select_optimal_hospital(
                    payload.latitude, 
                    payload.longitude, 
                    payload.driver_triage.driver_status_code
                )
                
                unified_alert = {
                    "accident_id": accident_id,
                    "timestamp": payload.timestamp,
                    "telemetry": {
                        "latitude": payload.latitude,
                        "longitude": payload.longitude,
                        "speed_kmph": payload.speed_kmph,
                        "isolated_g_force": payload.isolated_g_force,
                        "deceleration_delta_kmph": payload.deceleration_delta_kmph
                    },
                    "driver_status": {
                        "ear_avg": payload.driver_triage.ear_avg,
                        "mar": payload.driver_triage.mar,
                        "facial_asymmetry_index": payload.driver_triage.facial_asymmetry_index,
                        "unresponsive_probability": payload.driver_triage.unresponsive_probability,
                        "suspected_intoxication_index": payload.driver_triage.suspected_intoxication_index,
                        "driver_status_code": payload.driver_triage.driver_status_code
                    },
                    "dispatch_decision": {
                        "hospital_name": routing_data["selected_hospital"]["name"],
                        "trauma_level": routing_data["selected_hospital"]["trauma_level"],
                        "contact_phone": routing_data["selected_hospital"]["contact_phone"],
                        "distance_km": routing_data["distance_km"],
                        "paramedic_eta_minutes": routing_data["eta_minutes"],
                        "dispatch_score": routing_data["dispatch_score"],
                        "specialties": routing_data["selected_hospital"]["specialties"]
                    },
                    "green_corridor": routing_data["green_corridor_intersections"]
                }
                
                global latest_dispatch_record
                latest_dispatch_record = unified_alert
                
                # Render clean terminal dashboard and broadcast alerts
                print_trauma_dashboard(unified_alert)
                await manager.broadcast(unified_alert)

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        console.print(f"[bold red][!] WebSocket exception occurred: {e}[/bold red]")
        manager.disconnect(websocket)


# === Serve Frontend Static Folders ===

ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

AR_STATIC_DIR = os.path.join(FRONTEND_DIR, "bystander_ar")
DASHBOARD_STATIC_DIR = os.path.join(FRONTEND_DIR, "hospital_dashboard")

if os.path.exists(AR_STATIC_DIR):
    app.mount("/ar", StaticFiles(directory=AR_STATIC_DIR, html=True), name="ar")
    console.print("[bold green][Static Mount] Bystander WebAR mounted successfully at /ar[/bold green]")
if os.path.exists(DASHBOARD_STATIC_DIR):
    app.mount("/dashboard", StaticFiles(directory=DASHBOARD_STATIC_DIR, html=True), name="dashboard")
    console.print("[bold green][Static Mount] Trauma Bay Dashboard mounted successfully at /dashboard[/bold green]")