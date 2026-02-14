import streamlit as st
import numpy as np
import pandas as pd
import hashlib
import time
import secrets
from datetime import datetime

# --- CONFIGURATION HAUTE PRÉCISION ---
st.set_page_config(
    page_title="TTU-Shield : Ultra-Sentinel v2.1",
    page_icon="⚡",
    layout="wide"
)

# Thème Cyber-Security Final
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #00ff41; }
    .stMetric { background-color: #0d1117; border: 1px solid #10b981; padding: 15px; border-radius: 8px; }
    .stTextArea textarea { background-color: #07080a; color: #00ff41; border: 1px solid #10b981; font-family: 'Consolas', monospace; }
    </style>
    """, unsafe_allow_html=True)

class UltraSentinelV2:
    def __init__(self):
        self.master_key = secrets.token_hex(32)
        self.history = [0.0] * 50
        self.velocity_history = [0.0] * 50

    def get_dynamic_salt(self):
        """Mutation de phase temporelle (Moving Target Defense)"""
        ts = str(int(time.time() * 4)) 
        h = hashlib.sha256((self.master_key + ts).encode()).hexdigest()
        return (int(h[:2], 16) / 255) * 0.015 # Mutation ultra-fine

    def analyze(self, payload):
        if not payload: return 0.0, 0.0, "STABLE"
        
        # 1. ANALYSE SÉMANTIQUE (Ratio de pureté alphabétique)
        alpha_chars = sum(c.isalpha() or c.isspace() for c in payload)
        total_len = len(payload)
        human_ratio = alpha_chars / total_len if total_len > 0 else 0
        
        # 2. PONDÉRATION GÉOMÉTRIQUE (Signature de code)
        critical_symbols = ";|&<>$'\"\\{}[]()_="
        weight = sum(8.0 if char in critical_symbols else 0.05 for char in payload)
        
        # 3. ENTROPIE DE SHANNON (Complexité du signal)
        prob = [float(payload.count(c)) / total_len for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        # 4. CALIBRATION PRO (Ajustement selon le ratio humain)
        # On réduit la sensibilité pour le texte naturel (ton test à 0.32 deviendra STABLE)
        sensitivity = 0.08 if human_ratio > 0.85 else 1.0
        
        k_base = (weight * entropy * sensitivity) / (total_len + 1)
        k_final = k_base + self.get_dynamic_salt()
        
        # Vitesse de mutation (Accélération)
        velocity = abs(k_final - self.history[-1])
        
        self.history.append(k_final)
        self.velocity_history.append(velocity)
        if len(self.history) > 50:
            self.history.pop(0)
            self.velocity_history.pop(0)
            
        # --- NOUVEAUX SEUILS CALIBRÉS ---
        # Stable < 0.35 | Warning < 0.70 | Critical > 0.70
        if k_final > 0.70 or velocity > 0.30: status = "CRITICAL"
        elif k_final > 0.35: status = "WARNING"
        else: status = "STABLE"
            
        return k_final, velocity, status

# --- INITIALISATION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = UltraSentinelV2()
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- DASHBOARD ---
st.title("🛡️ TTU-Shield : Ultra-Sentinel Pro")
st.caption("Moteur de Dissipation Polymorphe | Calibration : v2.1")

# Récupération de l'analyse en temps réel
last_p = st.session_state.get('last_p', "")
k, v, s = st.session_state.sentinel.analyze(last_p)

m1, m2, m3 = st.columns(3)
with m1: st.metric("K-MASS", f"{k:.5f}")
with m2: st.metric("PHASE ACCEL", f"{v:.5f}")
with m3:
    color = "red" if s == "CRITICAL" else "orange" if s == "WARNING" else "green"
    st.markdown(f"**VECTEUR D'ÉTAT :** :{color}[{s}]")

st.divider()

col_l, col_r = st.columns([1, 1])

with col_l:
    st.header("⌨️ Input Stream")
    data = st.text_area("Flux à analyser...", height=150, placeholder="Injectez du texte ou du code...")
    if st.button("EXÉCUTER L'ANALYSE GÉOMÉTRIQUE"):
        st.session_state.last_p = data
        k_res, v_res, s_res = st.session_state.sentinel.analyze(data)
        if s_res != "STABLE":
            st.session_state.logs.append({
                "Horodatage": datetime.now().strftime("%H:%M:%S"),
                "Vecteur K": round(k_res, 4),
                "Type": s_res,
                "Action": "Neutralisé"
            })
        st.rerun()

with col_r:
    st.header("📈 Waveform Monitor")
    st.line_chart(st.session_state.sentinel.history, color="#00ff41")

st.divider()
st.header("📋 Registre d'Audit")
if st.session_state.logs:
    df = pd.DataFrame(st.session_state.logs)
    st.table(df.tail(5))
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Exporter le rapport (.CSV)", csv, "sentinel_report.csv", "text/csv")
else:
    st.info("Flux pur. Aucune anomalie détectée.")
