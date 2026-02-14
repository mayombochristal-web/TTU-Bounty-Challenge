import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import hashlib
import time
import secrets
from datetime import datetime

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(
    page_title="TTU-Shield : The Labyrinth", 
    page_icon="🌀", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Thème Cyber-Security Immersif
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

# --- MOTEUR DE DÉFENSE HOLONOME ---
class UltraSentinelLabyrinth:
    def __init__(self):
        self.master_key = secrets.token_hex(32)
        self.history_k = [0.0] * 50
        self.history_v = [0.0] * 50
        self.history_a = [0.0] * 50

    def get_dynamic_salt(self):
        """Mutation de phase temporelle (Moving Target Defense)"""
        ts = str(int(time.time() * 4)) 
        h = hashlib.sha256((self.master_key + ts).encode()).hexdigest()
        return (int(h[:2], 16) / 255) * 0.02

    def analyze_contextual(self, payload, context="message"):
        if not payload: return 0.0, 0.0, 0.0, "STABLE"
        
        # 1. ANALYSE SÉMANTIQUE
        alpha = sum(c.isalpha() or c.isspace() for c in payload)
        total = len(payload)
        h_ratio = alpha / total if total > 0 else 0
        
        # 2. MATRICE MULTI-INPUT
        weights = {
            "nom": {"sym": 20.0, "alpha": 0.01, "sens": 1.5},
            "email": {"sym": 10.0, "alpha": 0.05, "sens": 1.2},
            "message": {"sym": 8.0, "alpha": 0.05, "sens": 0.08 if h_ratio > 0.85 else 1.0}
        }
        cfg = weights.get(context, weights["message"])
        
        # 3. CALCUL DE MASSE (K)
        symbols = ";|&<>$'\"\\{}[]()_="
        w_score = sum(cfg["sym"] if char in symbols else cfg["alpha"] for char in payload)
        prob = [float(payload.count(c)) / total for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        k = ((w_score * entropy * cfg["sens"]) / (total + 1)) + self.get_dynamic_salt()
        
        # 4. VECTEURS DE PHASE (Vitesse et Accélération)
        v = abs(k - self.history_k[-1])
        a = abs(v - self.history_v[-1])
        
        # Mise à jour des registres
        self.history_k.append(k); self.history_v.append(v); self.history_a.append(a)
        for h in [self.history_k, self.history_v, self.history_a]: h.pop(0)

        # Seuils calibrés
        if k > 0.75 or v > 0.40: status = "CRITICAL"
        elif k > 0.35: status = "WARNING"
        else: status = "STABLE"
            
        return k, v, a, status

# --- GESTION DE LA SESSION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = UltraSentinelLabyrinth()
if 'trapped' not in st.session_state:
    st.session_state.trapped = False
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- MODE LABYRINTHE (PIÈGE) ---
if st.session_state.trapped:
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🌀 LABYRINTHE DE DISSIPATION ACTIVÉ</h1>", unsafe_allow_html=True)
    st.error("### DÉTECTION CRITIQUE : Votre signature a été capturée.")
    st.write("Le Sentinel a détecté une anomalie géométrique majeure. Votre flux a été redirigé vers un espace de stockage mort.")
    
    st.info("🔓 **BOUNTY CHALLENGE :** Pour sortir du labyrinthe et réinitialiser votre vecteur, témoignez de la robustesse de l'algorithme.")
    
    testimony = st.text_area("Expliquez pourquoi votre payload a été détecté...", placeholder="Mon injection a échoué car...")
    if st.button("ENVOYER LE TÉMOIGNAGE ET SORTIR"):
        if len(testimony) > 10:
            st.session_state.trapped = False
            st.session_state.logs.append({"Time": "N/A", "Vector K": "RESET", "Threat": "TESTIMONY", "Action": "Released"})
            st.success("Vecteur réaligné. Sortie autorisée.")
            st.rerun()
        else:
            st.warning("Témoignage trop court pour validation.")
    
    st.link_button("📢 Partager ma défaite sur X / Twitter", "https://twitter.com/intent/tweet?text=Mon%20attaque%20a%20été%20dissipée%20par%20le%20TTU-Shield.%20Impossible%20de%20contourner%20la%20géométrie%20de%20phase.")
    st.stop()

# --- INTERFACE PRINCIPALE ---
st.title("🛡️ TTU-Shield : Quantum Labyrinth")
st.markdown("*Bounty Challenge : Le premier système de sécurité qui utilise la géométrie de phase.*")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Matrix Config")
    context = st.selectbox("Type de champ", ["nom", "email", "message"])
    st.divider()
    st.markdown("### Métriques Live")
    k, v, a, s = st.session_state.sentinel.analyze_contextual(st.session_state.get('last_p', ""), context)
    st.write(f"**K-Mass:** `{k:.4f}`")
    st.write(f"**Status:** `{s}`")

# Layout
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("⌨️ Injection Stream")
    payload = st.text_area("Entrée de données...", height=200, placeholder="Tapez 'Bonjour' ou une injection SQL...")
    
    if st.button("SCANNER LE VECTEUR"):
        st.session_state.last_p = payload
        k_r, v_r, a_r, s_r = st.session_state.sentinel.analyze_contextual(payload, context)
        
        if s_r == "CRITICAL":
            st.session_state.trapped = True
            st.rerun()
        elif s_r == "WARNING":
            st.warning(f"⚠️ Anomalie détectée : Vecteur instable (k={k_r:.2f})")
            st.session_state.logs.append({"Time": datetime.now().strftime("%H:%M:%S"), "Vector K": round(k_r, 4), "Threat": s_r, "Action": "Alert"})
        else:
            st.success("✅ Flux stable. Information dissipée.")

with col_right:
    st.subheader("🔮 Sphère de Phase 3D")
    # Création du graphique Plotly avec correctif symbol='circle'
    fig = go.Figure(data=[go.Scatter3d(
        x=st.session_state.sentinel.history_k,
        y=st.session_state.sentinel.history_v,
        z=st.session_state.sentinel.history_a,
        mode='lines+markers',
        line=dict(color='#00ff41', width=3),
        marker=dict(size=4, color='#ff4b4b', symbol='circle', opacity=0.8)
    )])
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(title='Masse (K)', gridcolor='gray'),
            yaxis=dict(title='Vitesse (V)', gridcolor='gray'),
            zaxis=dict(title='Accel (A)', gridcolor='gray'),
            bgcolor="black"
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="black"
    )
    st.plotly_chart(fig, use_container_width=True)

# Logs Section
st.divider()
if st.session_state.logs:
    st.subheader("📋 Registre d'Audit")
    st.table(pd.DataFrame(st.session_state.logs).tail(5))
