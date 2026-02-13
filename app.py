import streamlit as st
import numpy as np
import pandas as pd
import hashlib
import time
from datetime import datetime

# --- CONFIGURATION PRO ---
st.set_page_config(
    page_title="TTU-Shield PRO : Moving Target Defense",
    page_icon="🛡️",
    layout="wide"
)

# Custom Cyber-Theme
st.markdown("""
    <style>
    .main { background-color: #07080a; color: #00ff41; }
    .stMetric { background-color: #11141a; border: 1px solid #00ff41; padding: 15px; border-radius: 5px; }
    .stTextArea textarea { background-color: #0d1117; color: #00ff41; border: 1px solid #00ff41; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTEUR TTU-SENTINEL PRO ---

class TTUSentinelPro:
    def __init__(self, master_key="TTU_SECRET_2024"):
        self.master_key = master_key
        self.history = [0.0] * 50
        self.velocity_history = [0.0] * 50

    def get_dynamic_mutation(self):
        """Crée une mutation temporelle incraquable (change 2x par seconde)"""
        time_salt = str(int(time.time() * 2)) 
        hash_val = hashlib.sha256((self.master_key + time_salt).encode()).hexdigest()
        # Micro-variation entre 0.001 et 0.009
        return int(hash_val[:4], 16) / 10000000

    def analyze(self, payload):
        if not payload: return 0.0, 0.0, "STABLE"
        
        # 1. Pondération Sémantique (Différencie Texte vs Code)
        symbols = ";|&<>$'\"\\{}[]()_="
        # Les symboles pèsent 20x plus que les lettres
        weight = sum(2.0 if char in symbols else 0.1 for char in payload)
        
        # 2. Calcul de l'Entropie Sémantique
        prob = [float(payload.count(c)) / len(payload) for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        # 3. Calcul du Vecteur Maître (Normalisé par la longueur)
        base_k = (weight * entropy) / (len(payload) + 1)
        
        # 4. Injection de la Mutation Temporelle (Le Shift Incraquable)
        mutation = self.get_dynamic_mutation()
        new_k = base_k + mutation
        
        # Calcul de la vitesse de phase (accélération du danger)
        dk_dt = abs(new_k - self.history[-1])
        
        # Mise à jour de l'historique
        self.history.append(new_k)
        self.velocity_history.append(dk_dt)
        if len(self.history) > 50:
            self.history.pop(0)
            self.velocity_history.pop(0)
            
        # Niveaux de Menace Pro
        if new_k > 0.80 or dk_dt > 0.25: return new_k, dk_dt, "CRITICAL"
        if new_k > 0.35 or dk_dt > 0.10: return new_k, dk_dt, "WARNING"
        return new_k, dk_dt, "STABLE"

# --- INITIALISATION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = TTUSentinelPro()
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- INTERFACE ---
st.title("🛡️ TTU-Shield PRO")
st.caption("Quantum Moving Target Defense | Statut : Bouclier Actif")

col1, col2, col3 = st.columns(3)
k_val, v_val, status = st.session_state.sentinel.analyze(st.session_state.get('last_p', ""))

with col1:
    st.metric("VECTEUR MAÎTRE (k)", f"{k_val:.5f}", help="Indice de mutation géométrique")
with col2:
    st.metric("RADAR DE PHASE", f"{v_val:.5f}", help="Vitesse de l'attaque")
with col3:
    color = "red" if status == "CRITICAL" else "orange" if status == "WARNING" else "green"
    st.markdown(f"**STATUT :** :{color}[{status}]")

st.divider()

c1, c2 = st.columns([1, 1])

with c1:
    st.header("⌨️ Input Stream")
    payload = st.text_area("Saisissez des données pour analyse...", height=150, key="input_area")
    
    if st.button("ANALYSER LE FLUX"):
        st.session_state.last_p = payload
        k, dk, lvl = st.session_state.sentinel.analyze(payload)
        
        if lvl != "STABLE":
            st.session_state.logs.append({
                "Horodatage": datetime.now().strftime("%H:%M:%S"),
                "Vecteur K": round(k, 4),
                "Type": lvl,
                "Alerte": "Tentative d'injection détectée" if lvl == "CRITICAL" else "Structure suspecte"
            })
        st.rerun()

with c2:
    st.header("📊 Géométrie du Signal")
    chart_data = pd.DataFrame({
        'Viscosité': st.session_state.sentinel.history,
        'Accélération': st.session_state.sentinel.velocity_history
    })
    st.line_chart(chart_data)

st.divider()
st.header("📋 Logs d'Audit de Sécurité")
if st.session_state.logs:
    st.table(pd.DataFrame(st.session_state.logs).tail(5))
else:
    st.info("Aucune anomalie enregistrée. Le flux est pur.")
