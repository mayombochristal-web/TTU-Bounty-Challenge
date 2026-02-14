import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import hashlib
import time
import secrets
import re
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="TTU-Shield : Autonomous Labyrinth", page_icon="🌀", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #00ff41; }
    .stMetric { background-color: #0d1117; border: 1px solid #00ff41; padding: 15px; border-radius: 8px; }
    .stTextArea textarea { background-color: #07080a; color: #00ff41; border: 1px solid #00ff41; font-family: 'Consolas', monospace; }
    h1, h2, h3 { color: #00ff41 !important; text-shadow: 0 0 10px #00ff41; }
    .stButton button { width: 100%; background-color: #0d1117; color: #00ff41; border: 1px solid #00ff41; height: 3em;}
    .stButton button:hover { background-color: #00ff41; color: black; }
    </style>
    """, unsafe_allow_html=True)

class AutonomousSentinel:
    def __init__(self):
        self.master_key = secrets.token_hex(32)
        self.history_k = [0.0] * 50
        self.history_v = [0.0] * 50
        self.history_a = [0.0] * 50
        self.depth = 0

    def auto_detect_context(self, payload):
        """Intelligence Artificielle de détection de contexte"""
        if re.match(r'^[0-9\s\+\-\(\)]+$', payload): return "numeric"
        if "@" in payload and "." in payload: return "email"
        if "/" in payload or "\\" in payload or "http" in payload: return "url_path"
        if len(payload.split()) < 3 and any(char.isdigit() for char in payload): return "id_field"
        return "message"

    def analyze(self, payload):
        if not payload: return 0.0, 0.0, 0.0, "STABLE", "none"
        
        ctx = self.auto_detect_context(payload)
        alpha = sum(c.isalpha() or c.isspace() for c in payload)
        total = len(payload)
        h_ratio = alpha / total if total > 0 else 0
        
        # MATRICE DE POIDS ÉVOLUÉE
        weights = {
            "numeric": {"sym": 40.0, "alpha": 15.0, "sens": 2.5},
            "email":    {"sym": 12.0, "alpha": 0.05, "sens": 1.2},
            "url_path": {"sym": 25.0, "alpha": 5.0,  "sens": 1.8},
            "id_field": {"sym": 45.0, "alpha": 20.0, "sens": 2.0},
            "message":  {"sym": 8.0,  "alpha": 0.05, "sens": 0.08 if h_ratio > 0.85 else 1.0}
        }
        cfg = weights.get(ctx)
        
        symbols = ";|&<>$'\"\\{}[]()_="
        w_score = sum(cfg["sym"] if char in symbols else cfg["alpha"] for char in payload)
        prob = [float(payload.count(c)) / total for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        k = ((w_score * entropy * cfg["sens"]) / (total + 1)) + (int(hashlib.sha256((self.master_key + str(time.time())).encode()).hexdigest()[:2], 16)/255 * 0.02)
        v = abs(k - self.history_k[-1])
        a = abs(v - self.history_v[-1])
        
        self.history_k.append(k); self.history_v.append(v); self.history_a.append(a)
        for h in [self.history_k, self.history_v, self.history_a]: h.pop(0)

        status = "CRITICAL" if (k > 0.75 or v > 0.45) else "WARNING" if k > 0.35 else "STABLE"
        return k, v, a, status, ctx

# --- SESSION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = AutonomousSentinel()
if 'last_payload' not in st.session_state:
    st.session_state.last_payload = ""

# --- DASHBOARD ---
k, v, a, s, ctx_detected = st.session_state.sentinel.analyze(st.session_state.last_payload)

st.title("🛡️ TTU-Shield : Autonomous Labyrinth")
m1, m2, m3, m4 = st.columns(4)
m1.metric("K-MASS", f"{k:.4f}")
m2.metric("CONTEXT DETECTED", ctx_detected.upper())
m3.metric("LABYRINTH DEPTH", st.session_state.sentinel.depth)
m4.metric("STATUS", s)

st.divider()

col_l, col_r = st.columns([1, 1.2])

with col_l:
    if st.session_state.sentinel.depth > 0:
        st.markdown(f"### 🌀 NIVEAU DE PROFONDEUR : {st.session_state.sentinel.depth}")
        st.error("Le Sentinel a verrouillé votre signature. Évasion impossible sans aveu.")
        
        tab1, tab2 = st.tabs(["S'enfoncer", "Se Rendre"])
        with tab1:
            p = st.text_area("Nouvelle tentative d'injection...", height=150)
            if st.button("LANCER L'ASSAUT"):
                st.session_state.last_payload = p
                k_r, v_r, a_r, s_r, c_r = st.session_state.sentinel.analyze(p)
                if s_r == "CRITICAL": st.session_state.sentinel.depth += 1
                st.rerun()
        with tab2:
            testimony = st.text_area("Témoignage de défaite :", placeholder="Pourquoi mon attaque a échoué...")
            if st.button("VALIDER L'AVEU"):
                if len(testimony) > 15:
                    st.session_state.sentinel.depth = 0
                    st.session_state.last_payload = ""
                    st.rerun()
    else:
        st.subheader("⌨️ Système d'Analyse Autonome")
        p = st.text_area("Entrez votre flux de données...", height=200, placeholder="Texte, Email, ID, SQL...")
        if st.button("EXÉCUTER L'AUDIT DE PHASE"):
            st.session_state.last_payload = p
            k_r, v_r, a_r, s_r, c_r = st.session_state.sentinel.analyze(p)
            if s_r == "CRITICAL": st.session_state.sentinel.depth = 1
            st.rerun()

with col_r:
    st.subheader("🔮 Visualisation Holonome 3D")
    fig = go.Figure(data=[go.Scatter3d(
        x=st.session_state.sentinel.history_k, y=st.session_state.sentinel.history_v, z=st.session_state.sentinel.history_a,
        mode='lines+markers',
        line=dict(color='#00ff41' if st.session_state.sentinel.depth == 0 else '#ff4b4b', width=4),
        marker=dict(size=4, color='#00ff41' if st.session_state.sentinel.depth == 0 else '#ff4b4b', symbol='circle')
    )])
    fig.update_layout(scene=dict(xaxis_title='K', yaxis_title='V', zaxis_title='A', bgcolor="black"),
                      margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor="black")
    st.plotly_chart(fig, use_container_width=True)
