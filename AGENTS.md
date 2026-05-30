You are an advanced, full-stack AI Solution Architect and Orchestration Agent. Your task is to build a production-ready, end-to-end prototype for the "Post-Crash Golden Hour Optimizer" platform. You must design this as a modular, containerized ecosystem broken down across 5 strict timeline phases.

Before writing code, execute the mandatory Prerequisites checklist.

\---

## PART 1: SYSTEM PREREQUISITES \& ENVIRONMENT SETUP

Do not skip this phase. Verify and install all necessary dependencies locally or within your execution sandbox:

1. System Dependencies: Ensure FFmpeg (for video/audio frame handling), Python 3.11+, and Node.js (v20+) are present.
2. Core Library Installations: Install `opencv-python`, `mediapipe`, `fastapi`, `uvicorn`, `websockets`, `pandas`, `numpy`, and `scikit-learn`.
3. Edge Sensors Initialization Script: Prepare a mock vehicle-telematics stream handling class capable of processing high-frequency spatial vectors.

\---

## PART 2: CORE WORKFLOW ARCHITECTURE

Implement the system sequentially across the following five functional blocks:

### Phase ①: Auto-Detect \& Anti-Gravity Filter (0-10 Seconds)

* Objective: Isolate crash impact forces from raw mobile device streams by deploying a gravity compensation low-pass filter.
* Schema: Process a data dictionary containing: `timestamp`, `latitude`, `longitude`, `speed\_kmph`, `accel\_x`, `accel\_y`, `accel\_z`.
* Algorithmic Math Logic:
Implement an anti-gravity filter to compute true linear acceleration vectors by dynamically tracking and subtracting the Earth's gravity vector ($9.81 m/s^2$):

  $$\\text{linear\_x} = \\text{accel\_x} - \\text{gravity\_x}$$
$$\\text{linear\_y} = \\text{accel\_y} - \\text{gravity\_y}$$
$$\\text{linear\_z} = \\text{accel\_z} - \\text{gravity\_z}$$

  Calculate total linear acceleration magnitude:
$$\\text{Total Magnitude} = \\sqrt{\\text{linear\_x}^2 + \\text{linear\_y}^2 + \\text{linear\_z}^2}$$
$$\\text{Isolated G-Force} = \\frac{\\text{Total Magnitude}}{9.81}$$

* Crash Flag Trigger: Set `predicted\_accident = 1` if the Isolated G-Force spikes above 4.0 G simultaneously with a severe deceleration delta in `speed\_kmph`.

  ### Phase ②: Driver Triage \& Sobriety Analysis (10-30 Seconds)

* Objective: Initialize local device camera burst frames upon `predicted\_accident == 1`.
* Feature Extraction: Apply MediaPipe Face Mesh coordinates to compute:

  1. Eye Aspect Ratio (EAR) to check for responsive blinking vs. closed/unconscious eyes.
  2. Mouth Aspect Ratio (MAR) to evaluate facial sagging or laxity.
* Classification Data: Output an evaluation prediction matrix calculating `unresponsive\_probability` and `suspected\_intoxication\_index`. Combine this with the coordinates to generate a unified JSON payload.

  ### Phase ③: Route Optimization \& Green-Corridor Dispatch (30-45 Seconds)

* Objective: Act as the backend router controller using Mapbox/Google Maps Matrix logic.
* Dispatch Algorithm: Calculate the optimal emergency response vehicle based on dynamic real-time traffic ETAs rather than geometric proximity.
* Corridors \& Capacity: Match coordinates against mock hospital emergency room data weights (Live bed occupancy, specialty availability). Simultaneously extract route coordinates to flag upcoming intersections, simulating a predictive traffic light preemption cycle ("Green Corridor").

  ### Phase ④: Bystander WebAR Guidance (Ongoing)

* Objective: Provide immediate life-support guidance using zero-install Web-AR technologies.
* Delivery: Mock an accessible HTML5/JS single-page application interface powered by `AR.js` or `A-Frame`. When a bystander accesses the URL with the vehicle ID parameter, instantiate the camera view to cast 3D animated direction graphics (e.g., chest compression vectors) directly over the camera feed.

  ### Phase ⑤: Hospital Prep \& Hand-off Panel

* Objective: Build an automated React or HTML dashboard panel for trauma bay staff.
* Execution: Stream the incoming data package continuously via WebSockets. If `predicted\_accident == 1`, render a red alert banner displaying structural crash telemetry, current paramedic ETA, and the driver status metrics compiled in Phase ②.

  \---

  ## PART 3: REVIEWS \& ARTIFACT GENERATION

1. Generate a structured file architecture framework outlining where the edge device script, cloud backend server, and front-end dashboard files live.
2. Produce clean, documented code blocks for each distinct layer. Focus heavily on executing Phase ① (The Anti-Gravity Python algorithm) and Phase ② (The JSON alerting data payload).
3. Do not abstract core logic components out of the scripts. Test the components using mock telemetry vectors and output the verification logs.

