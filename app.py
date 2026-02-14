import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import hashlib
import time
import secrets
from datetime import datetime

# --- CONFIGURATION LABYRINTHE ---
st.set_page_config(page_title="TTU-Shield : The Labyrinth", page_icon="🌀", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #05070a; color: #00ff41; }
    .stMetric { background-color: #0d1117; border: 1px solid #00ff41; padding: 15px; border-radius: 8px; }
    .stTextArea textarea { background-color: #07080a; color: #00ff41; border: 1px solid #00ff41; font-family: 'Consolas', monospace; }
    h1, h2, h3 { color: #00ff41 !important; text-shadow: 0 0 10px #00ff41; }
    .stButton button { width: 100%; background-color: #0d1117; color: #00ff41; border: 1px solid #00ff41; }
    .stButton button:hover { background-color: #00ff41; color: black; }
    </style>
    """, unsafe_allow_html=True)

class UltraSentinelLabyrinth:
    def __init__(self):
        self.master_key = secrets.token_hex(32)
        self.history_k = [0.0] * 50
        self.history_v = [0.0] * 50
        self.history_a = [0.0] * 50
        self.depth = 0 # Niveau d'enfoncement

    def analyze_contextual(self, payload, context="message"):
        if not payload: return 0.0, 0.0, 0.0, "STABLE"
        alpha = sum(c.isalpha() or c.isspace() for c in payload)
        total = len(payload)
        h_ratio = alpha / total if total > 0 else 0
        
        weights = {
            "nom": {"sym": 20.0, "alpha": 0.01, "sens": 1.5},
            "email": {"sym": 10.0, "alpha": 0.05, "sens": 1.2},
            "message": {"sym": 8.0, "alpha": 0.05, "sens": 0.08 if h_ratio > 0.85 else 1.0}
        }
        cfg = weights.get(context, weights["message"])
        
        symbols = ";|&<>$'\"\\{}[]()_="
        w_score = sum(cfg["sym"] if char in symbols else cfg["alpha"] for char in payload)
        prob = [float(payload.count(c)) / total for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        k = ((w_score * entropy * cfg["sens"]) / (total + 1)) + (int(hashlib.sha256((self.master_key + str(time.time())).encode()).hexdigest()[:2], 16)/255 * 0.02)
        v = abs(k - self.history_k[-1])
        a = abs(v - self.history_v[-1])
        
        self.history_k.append(k); self.history_v.append(v); self.history_a.append(a)
        if len(self.history_k) > 50: 
            for h in [self.history_k, self.history_v, self.history_a]: h.pop(0)

        if k > 0.75 or v > 0.40: status = "CRITICAL"
        elif k > 0.35: status = "WARNING"
        else: status = "STABLE"
            
        return k, v, a, status

# --- INITIALISATION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = UltraSentinelLabyrinth()
if 'last_payload' not in st.session_state:
    st.session_state.last_payload = ""

# --- DASHBOARD DE TÊTE (Toujours visible) ---
k, v, a, s = st.session_state.sentinel.analyze_contextual(st.session_state.last_payload, "message")

st.title("🛡️ TTU-Shield : Quantum Labyrinth")
c1, c2, c3, c4 = st.columns(4)
c1.metric("K-MASS (Masse)", f"{k:.4f}")
c2.metric("V-PHASE (Vitesse)", f"{v:.4f}")
c3.metric("LABYRINTH DEPTH", st.session_state.sentinel.depth)
c4.metric("STATUS", s)

st.divider()

# --- LAYOUT PRINCIPAL ---
col_input, col_viz = st.columns([1, 1.2])

with col_input:
    # Si l'attaquant est piégé
    if st.session_state.sentinel.depth > 0:
        st.markdown(f"### 🌀 PROFONDEUR NIVEAU {st.session_state.sentinel.depth}")
        st.error("Signature géométrique capturée. Vous êtes dans l'espace de dissipation.")
        
        action = st.radio("Choisissez votre issue :", 
                          ["S'enfoncer davantage (Continuer l'attaque)", "Se rendre (Témoigner de la robustesse)"])
        
        if action == "S'enfoncer davantage (Continuer l'attaque)":
            payload = st.text_area("Prochaine tentative d'injection...", height=150)
            if st.button("TENTER UNE ÉVASION"):
                st.session_state.last_payload = payload
                k_r, v_r, a_r, s_r = st.session_state.sentinel.analyze_contextual(payload, "message")
                if s_r == "CRITICAL":
                    st.session_state.sentinel.depth += 1
                st.rerun()
        
        else:
            testimony = st.text_area("Aveu de défaite pour réinitialisation :", placeholder="Expliquez pourquoi le Sentinel a gagné...")
            if st.button("ENVOYER ET QUITTER LE LABYRINTHE"):
                if len(testimony) > 10:
                    st.session_state.sentinel.depth = 0
                    st.session_state.last_payload = ""
                    st.success("Vecteur réaligné. Retour à la surface.")
                    st.rerun()
                else:
                    st.warning("Témoignage trop court pour une réinitialisation de phase.")
    
    # Mode Normal (Surface)
    else:
        st.subheader("⌨️ Injection Stream")
        payload = st.text_area("Entrée de données (Texte ou Code)", height=200)
        context = st.selectbox("Contexte du champ", ["nom", "email", "message"])
        
        if st.button("LANCER L'AUDIT"):
            st.session_state.last_payload = payload
            k_r, v_r, a_r, s_r = st.session_state.sentinel.analyze_contextual(payload, context)
            if s_r == "CRITICAL":
                st.session_state.sentinel.depth = 1
            st.rerun()

with col_viz:
    st.subheader("🔮 Visualisation Holonome 3D")
    # La sphère reste visible pour montrer la déformation
    fig = go.Figure(data=[go.Scatter3d(
        x=st.session_state.sentinel.history_k,
        y=st.session_state.sentinel.history_v,
        z=st.session_state.sentinel.history_a,
        mode='lines+markers',
        line=dict(color='#00ff41' if st.session_state.sentinel.depth == 0 else '#ff4b4b', width=4),
        marker=dict(size=4, color='#00ff41' if st.session_state.sentinel.depth == 0 else '#ff4b4b', symbol='circle')
    )])
    fig.update_layout(
        scene=dict(xaxis_title='K', yaxis_title='V', zaxis_title='A', bgcolor="black"),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="black"
    )
    st.plotly_chart(fig, use_container_width=True)
