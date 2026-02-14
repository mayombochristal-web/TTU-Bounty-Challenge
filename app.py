import streamlit as st
import numpy as np
import pandas as pd
import hashlib
import time
import secrets
from datetime import datetime

# --- CONFIGURATION HAUTE SÉCURITÉ ---
st.set_page_config(page_title="TTU-Shield : Ultra-Sentinel", page_icon="⚡", layout="wide")

class UltraSentinel:
    def __init__(self):
        self.master_key = secrets.token_hex(16)
        self.history = [0.05] * 50
        self.baseline_k = 0.15

    def get_dynamic_threshold(self):
        """Mutation temporelle : change toutes les 250ms pour empêcher le brute-force"""
        ts = str(int(time.time() * 4)) 
        h = hashlib.sha256((self.master_key + ts).encode()).hexdigest()
        return (int(h[:2], 16) / 255) * 0.05 # Variation subtile de 5%

    def analyze_pro(self, payload):
        if not payload: return 0.0, 0.0, "STABLE"
        
        # 1. FILTRE ANTI-FAUX POSITIFS (Le secret pour battre la concurrence)
        # On calcule le ratio lettres vs symboles
        letters = sum(c.isalpha() or c.isspace() for c in payload)
        total = len(payload)
        ratio_humain = letters / total if total > 0 else 0
        
        # 2. PONDÉRATION GÉOMÉTRIQUE
        symbols = ";|&<>$'\"\\{}[]()_="
        # Les symboles de code pèsent 50x plus qu'une lettre
        weight = sum(5.0 if char in symbols else 0.1 for char in payload)
        
        # 3. CALCUL DE L'ENTROPIE SHANNON
        prob = [float(payload.count(c)) / total for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        # 4. FORMULE MAÎTRESSE (Adaptative)
        # Si c'est du texte humain (ratio > 0.8), on réduit drastiquement la sensibilité
        sensitivity = 0.2 if ratio_humain > 0.8 else 1.0
        
        k_pure = (weight * entropy * sensitivity) / (total + 1)
        k_final = k_pure + self.get_dynamic_threshold()
        
        # Accélération (dk/dt)
        velocity = abs(k_final - self.history[-1])
        
        self.history.append(k_final)
        if len(self.history) > 50: self.history.pop(0)
        
        # SEUILS PRO
        if k_final > 0.75: status = "CRITICAL"
        elif k_final > 0.30: status = "WARNING"
        else: status = "STABLE"
            
        return k_final, velocity, status

# --- INTERFACE SAAS PROFESSIONNELLE ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = UltraSentinel()
if 'attack_logs' not in st.session_state:
    st.session_state.attack_logs = []

st.title("⚡ TTU-Shield : Ultra-Sentinel v2.0")
st.markdown("*Système de défense polymorphe par analyse de phase sémantique*")

# Dashboard Metrics
k_curr, v_curr, status = st.session_state.sentinel.analyze_pro(st.session_state.get('last_in', ""))

c1, c2, c3 = st.columns(3)
with c1: st.metric("K-VISCOSITY", f"{k_curr:.4f}")
with c2: st.metric("PHASE VELOCITY", f"{v_curr:.4f}")
with c3: st.metric("SHIELD STATE", status)

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🌐 Traffic Monitor")
    user_input = st.text_area("Simuler un flux entrant (Texte ou Code)", height=150)
    if st.button("SCANNER LE FLUX"):
        st.session_state.last_in = user_input
        k, v, s = st.session_state.sentinel.analyze_pro(user_input)
        if s != "STABLE":
            st.session_state.attack_logs.append({
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Vector": round(k, 4),
                "Threat": s,
                "Action": "Dissipated"
            })
        st.rerun()

with col_right:
    st.subheader("📈 Quantum Waveform")
    st.area_chart(st.session_state.sentinel.history, color="#00ff41")

if st.session_state.attack_logs:
    st.subheader("🚨 Incident Response Logs")
    st.dataframe(pd.DataFrame(st.session_state.attack_logs).tail(5), use_container_width=True)
