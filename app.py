import math
import random
import time
import pandas as pd
import streamlit as st
from collections import deque

st.set_page_config(page_title="DRDO RCI Telemetry Ground Station", layout="wide")

st.title("🛰️ Avionics Telemetry Ground Station")
st.caption("DRDO RCI Internship Project | Real-Time Flight Dynamics, Safety Monitoring & Mission Control")

# Mission state initialization
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "crashed" not in st.session_state:
    st.session_state.crashed = False
if "history" not in st.session_state:
    st.session_state.history = deque(maxlen=40)
    st.session_state.pkt = 0
    st.session_state.t = 0.0
    st.session_state.altitude = 500.0
    st.session_state.velocity = 200.0

def reset_mission():
    st.session_state.is_running = False
    st.session_state.crashed = False
    st.session_state.history.clear()
    st.session_state.pkt = 0
    st.session_state.t = 0.0
    st.session_state.altitude = 500.0
    st.session_state.velocity = 200.0

# Mission Control Panel
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 4])

with col_ctrl1:
    if not st.session_state.is_running:
        if st.button("🚀 Start Mission", type="primary", use_container_width=True, disabled=st.session_state.crashed):
            st.session_state.is_running = True
            st.rerun()
    else:
        if st.button("⏸️ Pause Mission", use_container_width=True):
            st.session_state.is_running = False
            st.rerun()

with col_ctrl2:
    if st.button("🔄 Respawn Flight", use_container_width=True):
        reset_mission()
        st.rerun()

# Flight Dynamics Simulation
if st.session_state.is_running and not st.session_state.crashed:
    st.session_state.pkt += 1
    st.session_state.t += 0.5
    t = st.session_state.t

    # Realistic parabolic trajectory: Climb -> Apogee -> Descent
    if t < 25:
        # Boost / Climb Phase
        vertical_rate = 180.0 - (t * 4.0)
        st.session_state.velocity = 300.0 + (t * 8.0)
        pitch = 35.0 - (t * 1.2) + random.uniform(-0.5, 0.5)
    else:
        # Descent / Terminal Dive Phase
        vertical_rate = -50.0 - ((t - 25) * 12.0)
        st.session_state.velocity = 450.0 + ((t - 25) * 10.0)
        pitch = -25.0 - ((t - 25) * 1.5) + random.uniform(-1.0, 1.0)

    st.session_state.altitude += vertical_rate * 0.5 + random.uniform(-2.0, 2.0)
    roll = 6.0 * math.sin(t * 0.4) + random.uniform(-0.3, 0.3)

    # Check for Ground Impact
    if st.session_state.altitude <= 0.0:
        st.session_state.altitude = 0.0
        st.session_state.velocity = 0.0
        pitch = 0.0
        roll = 0.0
        st.session_state.crashed = True
        st.session_state.is_running = False

    st.session_state.history.append({
        "Packet": st.session_state.pkt,
        "Time (s)": round(t, 1),
        "Altitude (m)": round(max(0.0, st.session_state.altitude), 1),
        "Velocity (m/s)": round(st.session_state.velocity, 1),
        "Pitch (deg)": round(pitch, 2),
        "Roll (deg)": round(roll, 2)
    })

# Danger / Crash Status Banner
if st.session_state.crashed:
    st.error("💥 CRITICAL ALERT: IMPACT DETECTED! Flight vehicle has crashed. Use 'Respawn Flight' to re-initialize.")
elif st.session_state.is_running:
    if st.session_state.altitude < 1200.0 and st.session_state.t > 20:
        st.error("🚨 DANGER WARNING: TERRAIN PROXIMITY! Descent rate critical — crash imminent!")
    elif st.session_state.altitude < 3000.0 and st.session_state.t > 20:
        st.warning("⚠️ CAUTION: Vehicle descending rapidly below 3000m threshold.")
    else:
        st.success("🟢 Flight telemetry normal. Systems nominal.")
else:
    st.info("System Standby. Click 'Start Mission' to launch trajectory streaming.")

# Top Telemetry Metrics
df = pd.DataFrame(list(st.session_state.history))

c1, c2, c3, c4 = st.columns(4)
if not df.empty:
    cur = df.iloc[-1]
    c1.metric("Altitude", f"{cur['Altitude (m)']} m")
    c2.metric("Velocity", f"{cur['Velocity (m/s)']} m/s")
    c3.metric("Attitude (Pitch / Roll)", f"{cur['Pitch (deg)']}° / {cur['Roll (deg)']}°")
    c4.metric("Total Packets", int(cur['Packet']))
else:
    c1.metric("Altitude", "500.0 m")
    c2.metric("Velocity", "200.0 m/s")
    c3.metric("Attitude (Pitch / Roll)", "0.0° / 0.0°")
    c4.metric("Total Packets", 0)

# Charts
col1, col2 = st.columns(2)
with col1:
    st.subheader("Flight Altitude Trajectory (m)")
    if not df.empty:
        st.line_chart(df.set_index("Time (s)")["Altitude (m)"], height=260)
    else:
        st.write("Awaiting telemetry link...")

with col2:
    st.subheader("Attitude Vectors (Pitch / Roll)")
    if not df.empty:
        st.line_chart(df.set_index("Time (s)")[["Pitch (deg)", "Roll (deg)"]], height=260)
    else:
        st.write("Awaiting telemetry link...")

# Packet Data Buffer
st.subheader("Recent Decoded Telemetry Packets")
if not df.empty:
    st.dataframe(df.tail(6), use_container_width=True)

# Loop update when active
if st.session_state.is_running and not st.session_state.crashed:
    time.sleep(0.3)
    st.rerun()