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

# CSS Cyber-Guerre
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #00ff41; }
    .stMetric { background-color: #0d1117; border: 1px solid #00ff41; padding: 15px; border-radius: 8px; }
    .stTextArea textarea { background-color: #07080a; color: #00ff41; border: 1px solid #00ff41; font-family: 'Consolas', monospace; }
    h1, h2, h3 { color: #00ff41 !important; text-shadow: 0 0 10px #00ff41; }
    </style>
    """, unsafe_allow_html=True)

class UltraSentinelLabyrinth:
    def __init__(self):
        self.master_key = secrets.token_hex(32)
        self.history_k = [0.0] * 50
        self.history_v = [0.0] * 50
        self.history_a = [0.0] * 50 # Accélération (Jerk)

    def get_dynamic_salt(self):
        ts = str(int(time.time() * 4)) 
        h = hashlib.sha256((self.master_key + ts).encode()).hexdigest()
        return (int(h[:2], 16) / 255) * 0.02

    def analyze_contextual(self, payload, context="message"):
        if not payload: return 0.0, 0.0, 0.0, "STABLE"
        
        # 1. MATRICE MULTI-INPUT (Sensibilité par contexte)
        alpha = sum(c.isalpha() or c.isspace() for c in payload)
        total = len(payload)
        h_ratio = alpha / total if total > 0 else 0
        
        # Profils de sensibilité
        weights = {
            "nom": {"sym": 20.0, "alpha": 0.01, "sens": 1.5},
            "email": {"sym": 10.0, "alpha": 0.05, "sens": 1.2},
            "message": {"sym": 8.0, "alpha": 0.05, "sens": 0.08 if h_ratio > 0.85 else 1.0}
        }
        cfg = weights.get(context, weights["message"])
        
        # 2. CALCUL GÉOMÉTRIQUE
        symbols = ";|&<>$'\"\\{}[]()_="
        w_score = sum(cfg["sym"] if char in symbols else cfg["alpha"] for char in payload)
        
        prob = [float(payload.count(c)) / total for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        k = ((w_score * entropy * cfg["sens"]) / (total + 1)) + self.get_dynamic_salt()
        
        # 3. VECTEURS DE PHASE (Vitesse et Accélération)
        v = abs(k - self.history_k[-1])
        a = abs(v - self.history_v[-1])
        
        self.history_k.append(k); self.history_v.append(v); self.history_a.append(a)
        if len(self.history_k) > 50: 
            for h in [self.history_k, self.history_v, self.history_a]: h.pop(0)

        # SEUILS DU LABYRINTHE
        if k > 0.75 or v > 0.40: status = "CRITICAL"
        elif k > 0.35: status = "WARNING"
        else: status = "STABLE"
            
        return k, v, a, status

# --- LOGIQUE DE SESSION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = UltraSentinelLabyrinth()
if 'trapped' not in st.session_state:
    st.session_state.trapped = False

# --- ÉCRAN DU LABYRINTHE (PIÈGE) ---
if st.session_state.trapped:
    st.markdown("<h1 style='text-align: center; color: red;'>🌀 LABYRINTHE DE DISSIPATION</h1>", unsafe_allow_html=True)
    st.error(f"### ACCÈS REFUSÉ : Votre signature géométrique est instable.")
    st.write("Le Sentinel a détecté une torsion de phase. Votre payload a été dissipé dans un espace de Hilbert.")
    
    st.info("🔓 **TÉMOIGNAGE REQUIS :** Pour réinitialiser votre vecteur et sortir du labyrinthe, vous devez témoigner de la robustesse de l'algorithme.")
    
    testimony = st.text_area("Expliquez pourquoi votre attaque a échoué...")
    if st.button("ENVOYER LE TÉMOIGNAGE ET RESET"):
        st.session_state.trapped = False
        st.success("Vecteur réinitialisé. Sortie du labyrinthe autorisée.")
        st.rerun()
    
    st.link_button("📢 Twitter / X : Déclarer sa défaite", f"https://twitter.com/intent/tweet?text=Mon%20attaque%20a%20été%20pulvérisée%20par%20le%20TTU-Shield%20!%20Impossible%20de%20contourner%20la%20géométrie%20de%20phase.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
st.title("🛡️ TTU-Shield : Quantum Labyrinth")
st.markdown("*Bounty Challenge : Défiez le Sentinel. Si vous échouez, vous entrez dans le labyrinthe.*")

# Matrice Multi-Input
with st.sidebar:
    st.header("⚙️ Configuration Matrix")
    context = st.selectbox("Contexte du champ", ["nom", "email", "message"])
    st.divider()
    st.write("**Mode :** Piège Actif")
    st.write("**Algorithme :** Holonome V3")

# Inputs
col_input, col_viz = st.columns([1, 1.2])

with col_input:
    st.subheader("⌨️ Injection Stream")
    alias = st.text_input("Alias Hacker", "Spectre_Alpha")
    payload = st.text_area("Entrée (SQL, Code, Script...)", height=200)
    
    if st.button("TENTER L'INTRUSION"):
        k, v, a, s = st.session_state.sentinel.analyze_contextual(payload, context)
        if s == "CRITICAL":
            st.session_state.trapped = True
            st.rerun()
        elif s == "WARNING":
            st.warning(f"⚠️ Alerte de phase : Mutation suspecte détectée (k={k:.2f})")
        else:
            st.success("✅ Information dissipée. Aucune torsion détectée.")

with col_viz:
    st.subheader("🔮 Visualisation Holonome 3D")
    # Sphère de Phase 3D
    fig = go.Figure(data=[go.Scatter3d(
        x=st.session_state.sentinel.history_k,
        y=st.session_state.sentinel.history_v,
        z=st.session_state.sentinel.history_a,
        mode='lines+markers',
        line=dict(color='#00ff41', width=4),
        marker=dict(size=4, color='#ff4b4b', symbol='sphere')
    )])
    fig.update_layout(
        scene=dict(
            xaxis_title='Masse (K)',
            yaxis_title='Vitesse (V)',
            zaxis_title='Accélération (A)',
            bgcolor="black"
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="black"
    )
    st.plotly_chart(fig, use_container_width=True)

# Dashboard Métriques
st.divider()
k, v, a, s = st.session_state.sentinel.analyze_contextual(payload, context)
c1, c2, c3, c4 = st.columns(4)
c1.metric("K-MASS", f"{k:.4f}")
c2.metric("V-PHASE", f"{v:.4f}")
c3.metric("A-JERK", f"{a:.4f}")
c4.metric("STATUS", s)
