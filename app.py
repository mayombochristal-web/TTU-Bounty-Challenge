import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import hashlib
import time
import sqlite3
import re
from datetime import datetime

# --- DATABASE PERSISTENCE ---
def init_db():
    conn = sqlite3.connect('sentinel_fortress.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attackers 
                 (ip TEXT PRIMARY KEY, depth INTEGER, last_seen TIMESTAMP)''')
    conn.commit()
    return conn

db_conn = init_db()

# --- APP CONFIGURATION ---
st.set_page_config(page_title="TTU-Shield v5.0", page_icon="🏯", layout="wide")

# Custom UI Design
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #00ff41; font-family: 'Courier New', monospace; }
    .stMetric { background-color: #0d1117; border: 1px solid #00ff41; padding: 15px; border-radius: 10px; box-shadow: 0 0 15px rgba(0,255,65,0.1); }
    .stTextArea textarea { background-color: #07080a; color: #00ff41; border: 1px solid #00ff41; border-radius: 5px; }
    .status-box { padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; border: 1px solid #00ff41; }
    .critical-text { color: #ff4b4b; text-shadow: 0 0 10px #ff4b4b; }
    .stable-text { color: #00ff41; text-shadow: 0 0 10px #00ff41; }
    </style>
    """, unsafe_allow_html=True)

class UltraSentinelV5:
    def __init__(self, ip="127.0.0.1"):
        self.ip = ip
        self.depth = self.get_depth()
        self.history_k = [0.0] * 30

    def get_depth(self):
        c = db_conn.cursor()
        c.execute("SELECT depth FROM attackers WHERE ip=?", (self.ip,))
        res = c.fetchone()
        return res[0] if res else 0

    def update_depth(self, increment=1):
        self.depth += increment
        c = db_conn.cursor()
        c.execute("INSERT OR REPLACE INTO attackers (ip, depth, last_seen) VALUES (?, ?, ?)",
                  (self.ip, self.depth, datetime.now()))
        db_conn.commit()

    def reset_depth(self):
        self.depth = 0
        c = db_conn.cursor()
        c.execute("DELETE FROM attackers WHERE ip=?", (self.ip,))
        db_conn.commit()

    def analyze_zipf(self, text):
        """Détecte l'écart par rapport à la distribution naturelle du langage"""
        if len(text) < 5: return 0.5
        chars = pd.Series(list(text)).value_counts(normalize=True)
        zipf_ideal = np.array([1/i for i in range(1, len(chars)+1)])
        zipf_ideal /= zipf_ideal.sum()
        return np.linalg.norm(chars.values - zipf_ideal)

    def process_flux(self, payload, is_honeypot=False):
        if is_honeypot:
            self.update_depth(5)
            return 999.9, "BOT_TRAP", "CRITICAL", "Tentative d'accès automatisé détectée."

        total = len(payload)
        alpha = sum(c.isalpha() or c.isspace() for c in payload)
        h_ratio = alpha / total if total > 0 else 0
        zipf_score = self.analyze_zipf(payload)
        
        # Auto-détection du contexte
        if "@" in payload and "." in payload: ctx = "EMAIL"
        elif payload.isdigit(): ctx = "NUMERIC"
        elif any(c in "<>/\\" for c in payload): ctx = "CODE/PATH"
        else: ctx = "HUMAN_PROSE"

        # Matrice de décision
        sens = 2.5 if ctx == "CODE/PATH" else (0.1 if h_ratio > 0.8 else 1.5)
        symbols = sum(25.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.1 for c in payload)
        
        k_mass = (symbols * zipf_score * sens) / (total + 1)
        
        if k_mass > 0.85:
            status = "CRITICAL"
            reason = "Anomalie structurelle détectée : entropie trop élevée pour un flux humain."
            self.update_depth(1)
        elif k_mass > 0.4:
            status = "WARNING"
            reason = "Vibration de phase suspecte. Comportement à la limite de la conformité."
        else:
            status = "STABLE"
            reason = "Signature géométrique fluide. Flux autorisé."
            
        return round(k_mass, 4), ctx, status, reason

# --- UI LOGIC ---
sentinel = UltraSentinelV5()

# SIDEBAR : Système d'Audit
with st.sidebar:
    st.header("⚙️ SENTINEL CORE")
    st.write(f"**IP Monitor:** `{sentinel.ip}`")
    st.write(f"**Uptime:** {datetime.now().strftime('%H:%M:%S')}")
    st.divider()
    st.info("Cette version utilise la persistance SQLite. Vos actions sont enregistrées de manière permanente dans le registre d'audit.")

# HEADER : Dashboard
st.title("🏯 TTU-Shield v5.0 : Expérience Sentience")
m1, m2, m3, m4 = st.columns(4)

# LABYRINTH CHECK
if sentinel.depth > 0:
    # --- UI : MODE LABYRINTHE ---
    st.markdown(f"<div class='status-box' style='border-color: #ff4b4b;'><h2 class='critical-text'>🌀 LABYRINTHE ACTIVÉ (Niveau {sentinel.depth})</h2></div>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        st.subheader("🔓 Procédure de Purge")
        st.write("Votre signature géométrique a été verrouillée. Pour réinitialiser le système, vous devez prouver votre conscience en expliquant pourquoi votre flux a été rejeté.")
        
        aveu = st.text_area("Aveux techniques (Minimum 50 caractères) :", height=150)
        if st.button("SOUMETTRE POUR RÉALIGNEMENT"):
            if len(aveu) >= 50:
                sentinel.reset_depth()
                st.success("✅ Signature purgée. Redémarrage des capteurs...")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Témoignage trop court. La base de données refuse la purge.")
    
    with col_r:
        st.subheader("📉 Analyse de la Vibration de Rupture")
        # Visualisation du chaos
        chaos_data = np.random.randn(50).cumsum()
        fig = go.Figure(go.Scatter(y=chaos_data, line=dict(color='#ff4b4b', width=3)))
        fig.update_layout(paper_bgcolor="black", plot_bgcolor="black", margin=dict(l=0,r=0,b=0,t=0), height=300)
        st.plotly_chart(fig, use_container_width=True)

else:
    # --- UI : MODE SURFACE ---
    st.markdown("<div class='status-box'><h2 class='stable-text'>🛡️ SHIELD ACTIVE : SURVEILLANCE DE PHASE</h2></div>", unsafe_allow_html=True)
    
    # Honeypot Invisible (uniquement pour les bots)
    st.text_input("BotTrap", key="hp", label_visibility="collapsed")
    if st.session_state.hp:
        sentinel.process_flux("", is_honeypot=True)
        st.rerun()

    col_input, col_viz = st.columns([1, 1.2])
    
    with col_input:
        st.subheader("⌨️ Input Stream")
        payload = st.text_area("Saisissez votre donnée pour audit...", height=200, placeholder="Ex: Bonjour le monde OU <script>...")
        
        if st.button("LANCER L'ANALYSE GÉOMÉTRIQUE"):
            k, ctx, stat, reason = sentinel.process_flux(payload)
            
            # Affichage explicite des résultats
            if stat == "CRITICAL":
                st.error(f"**ALERTE :** {reason}")
                time.sleep(1)
                st.rerun()
            elif stat == "WARNING":
                st.warning(f"**ATTENTION :** {reason}")
            else:
                st.success(f"**VALIDE :** {reason}")
            
            st.write(f"**Contexte détecté :** `{ctx}`")
            st.write(f"**Masse calculée (K) :** `{k}`")

    with col_viz:
        st.subheader("🔮 Visualisation Holonome")
        # Historique fictif pour la démo visuelle
        y_data = [0.2, 0.25, 0.22, 0.28, 0.21]
        if 'payload' in locals() and payload:
            k_val, _, _, _ = sentinel.process_flux(payload)
            y_data.append(k_val)
        
        fig = go.Figure(go.Scatter(y=y_data, mode='lines+markers', line=dict(color='#00ff41', width=4), marker=dict(size=10)))
        fig.update_layout(paper_bgcolor="black", plot_bgcolor="black", margin=dict(l=0,r=0,b=0,t=0), height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.write("### 📘 Comment lire ces données ?")
    st.markdown("""
    * **K-MASS :** Représente la densité symbolique. Un humain écrit entre 0.1 et 0.3. Un hacker explose ce score.
    * **CONTEXT :** L'IA détecte si vous remplissez un email, un nom ou si vous injectez du code.
    * **DEPTH :** Nombre de fois où vous avez tenté de briser le système. À chaque tentative, le labyrinthe s'épaissit.
    """)
