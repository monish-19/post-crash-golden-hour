import streamlit as st
import requests
import time

st.set_page_config(
    page_title="Post-Crash Golden Hour Core",
    page_icon="🚑",
    layout="wide"
)

st.markdown("""
    <style>
        .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #ef4444; }
        .reportview-container { background: #0e1117; }
        .stTable { background-color: #111827; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🚑 Post-Crash Golden Hour Emergency Command Center")
st.subheader("Real-Time Telematics Ingestion & IoT Smart City Router")
st.write("---")

st.sidebar.header("🎮 Presentation Controls")
st.sidebar.write("Select a scenario to simulate an active vehicle crash stream:")

scenario = st.sidebar.radio(
    "Active Scenario Simulation Input",
    ["Select Scenario...", "Case A: Critical Crash (Unconscious)", "Case B: Minor Collision (Responsive)"]
)

if scenario == "Case A: Critical Crash (Unconscious)":
    status_text = "🚨 CRITICAL UNCONSCIOUS"
    g_force = "6.83 G"
    ear = "0.08"
    mar = "0.56"
    prob = "100%"
    hospital = "Mercy General Hospital (Trauma Level 1)"
    eta = "1.5 Minutes"
    
    traffic_data = [
        {"Intersection Node": "Junction Alpha (Ring Road)", "Coordinates": "37.7762, -122.4170", "Signal Action": "🟢 FORCE GREEN (Preempting)"},
        {"Intersection Node": "Junction Beta (Broadway St)", "Coordinates": "37.7775, -122.4147", "Signal Action": "🟢 FORCE GREEN (Preempting)"},
        {"Intersection Node": "Junction Gamma (Trauma Way)", "Coordinates": "37.7788, -122.4124", "Signal Action": "🟢 FORCE GREEN (Preempting)"}
    ]

elif scenario == "Case B: Minor Collision (Responsive)":
    status_text = "✅ RESPONSIVE (Stable State)"
    g_force = "1.20 G"
    ear = "0.58"
    mar = "0.25"
    prob = "2.0%"
    hospital = "City Memorial Hospital (Trauma Level 2)"
    eta = "2.11 Minutes"
    
    traffic_data = [
        {"Intersection Node": "Junction Alpha (Ring Road)", "Coordinates": "37.7724, -122.4220", "Signal Action": "🟡 HOLD CLEARING CURRENT PHASE"},
        {"Intersection Node": "Junction Beta (Broadway St)", "Coordinates": "37.7700, -122.4247", "Signal Action": "⚪ NO OVERRIDE REQUIRED"},
        {"Intersection Node": "Junction Gamma (Trauma Way)", "Coordinates": "37.7675, -122.4274", "Signal Action": "⚪ NO OVERRIDE REQUIRED"}
    ]

if scenario != "Select Scenario...":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Impact Force", value=g_force)
    with col2:
        st.metric(label="Driver State Feedback", value=status_text)
    with col3:
        st.metric(label="Eye Aspect Ratio (EAR)", value=ear)
    with col4:
        st.metric(label="Unresponsive Probability", value=prob)
        
    st.write("---")
    left_panel, right_panel = st.columns([1, 1])
    
    with left_panel:
        st.subheader("🏥 Algorithmic Hospital Allocation Match")
        st.info(f"**Target Facility Assigned:** {hospital}")
        st.success(f"⏱️ **Dynamic Emergency Transit ETA:** {eta}")
        st.markdown("""
        * **Specialized Wing Selection:** Neurological/Cardiac Resuscitation Team Alerted.
        * **Resource Status:** ICU Bed locked and allocated on ingestion handshake.
        """)
        
    with right_panel:
        st.subheader("🚦 Smart City IoT Green Corridor Override")
        st.write("Live Traffic Intersections pre-emption statuses:")
        st.table(traffic_data)
else:
    st.info("💡 Presenter Prompt: Please pick an active telemetry scenario from the left sidebar control panel to stream real-time data onto the web dashboard!")
