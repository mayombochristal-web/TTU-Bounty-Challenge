import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import hashlib
import time
import sqlite3
import re
from datetime import datetime

# --- INITIALISATION DE LA BASE DE DONNÉES (PERSISTENCE) ---
def init_db():
    conn = sqlite3.connect('sentinel_fortress.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attackers 
                 (ip TEXT PRIMARY KEY, depth INTEGER, testimony TEXT, last_seen TIMESTAMP)''')
    conn.commit()
    return conn

conn = init_db()

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="TTU-Shield v4 : Iron-Labyrinth", page_icon="🏯", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #030507; color: #00ff41; }
    .stMetric { background-color: #0a0e14; border: 1px solid #00ff41; box-shadow: 0 0 10px #00ff4133; }
    .stTextArea textarea { background-color: #05070a; color: #00ff41; border: 1px solid #ff4b4b; }
    .hidden-trap { display: none; }
    </style>
    """, unsafe_allow_html=True)

class IronSentinel:
    def __init__(self, ip):
        self.ip = ip
        self.load_status()
        self.history_k = [0.0] * 50

    def load_status(self):
        c = conn.cursor()
        c.execute("SELECT depth FROM attackers WHERE ip=?", (self.ip,))
        row = c.fetchone()
        self.depth = row[0] if row else 0

    def update_db(self):
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO attackers (ip, depth, last_seen) VALUES (?, ?, ?)",
                  (self.ip, self.depth, datetime.now()))
        conn.commit()

    def analyze_frequency(self, payload):
        """Analyse de la Loi de Zipf (détection de code vs langue)"""
        counts = pd.Series(list(payload)).value_counts()
        expected = np.array([1/i for i in range(1, len(counts)+1)])
        actual = counts.values / counts.values.sum()
        # Plus l'écart est grand, plus c'est du code/obfuscation
        return np.linalg.norm(actual - expected[:len(actual)])

    def analyze_autonomous(self, payload, honey_val=""):
        if honey_val: # LE PIÈGE HONEYPOT
            self.depth += 5
            return 999.9, "HONEYPOT_TRAP", "CRITICAL"

        alpha = sum(c.isalpha() or c.isspace() for c in payload)
        total = len(payload)
        h_ratio = alpha / total if total > 0 else 0
        freq_anomaly = self.analyze_frequency(payload)
        
        # Détection de contexte par structure
        if "@" in payload: ctx = "EMAIL"
        elif payload.isdigit(): ctx = "NUMERIC"
        elif any(c in "/\\" for c in payload): ctx = "SYSTEM_PATH"
        else: ctx = "GENERAL"

        # Matrice de poids dynamique
        sens = 2.0 if ctx != "GENERAL" else (0.1 if h_ratio > 0.8 else 1.5)
        
        # Calcul de Masse K augmenté par l'anomalie de fréquence
        symbols = ";|&<>$'\"\\{}[]()_="
        sym_score = sum(30.0 if c in symbols else 0.1 for c in payload)
        
        k = ((sym_score * freq_anomaly * sens) / (total + 1))
        
        status = "CRITICAL" if k > 0.8 else "STABLE"
        if status == "CRITICAL":
            self.depth += 1
            self.update_db()
            
        return k, ctx, status

# --- LOGIQUE DE L'APPLICATION ---
user_ip = "127.0.0.1" # En prod, utiliser les headers pour la vraie IP
sentinel = IronSentinel(user_ip)

st.title("🏯 TTU-Shield v4 : Iron-Labyrinth")
st.caption("Système de Défense Autonome avec Persistance SQLite & Analyse Fréquentielle")

# --- ÉCRAN DU LABYRINTHE PERSISTANT ---
if sentinel.depth > 0:
    st.error(f"🛑 IDENTITÉ VERROUILLÉE DANS LA BASE DE DONNÉES (Niveau {sentinel.depth})")
    
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Soumission de Témoignage")
        st.info("Votre adresse IP est marquée. Seul un aveu technique peut purger votre signature.")
        testimony = st.text_area("Expliquez votre intention d'attaque...", height=200)
        if st.button("PURGER LA SIGNATURE"):
            if len(testimony) > 50:
                sentinel.depth = 0
                sentinel.update_db()
                st.success("Base de données mise à jour. Redémarrage du système...")
                st.rerun()
            else:
                st.warning("Témoignage insuffisant pour une purge de grade 4.")
    
    with col2:
        st.subheader("Traceur de Phase")
        # On simule un graphique de chaos pour l'attaquant
        noise = np.random.normal(0, sentinel.depth, 50)
        fig = go.Figure(go.Scatter(y=noise, line=dict(color='red')))
        fig.update_layout(title="Vibration de Phase (Capturée)", paper_bgcolor="black", plot_bgcolor="black")
        st.plotly_chart(fig)
    st.stop()

# --- INTERFACE DE SURFACE ---
c1, c2, c3 = st.columns(3)
c1.metric("STATUS", "SHIELD ACTIVE")
c2.metric("THREAT LEVEL", "MONITORED")
c3.metric("DB ENTRIES", "SECURED")

st.divider()

# Champ Honeypot (Invisible pour l'humain, visible pour le bot)
honey_trap = st.text_input("Username (Leave empty)", key="hp", label_visibility="hidden")
if honey_trap:
    sentinel.analyze_autonomous("", honey_val=honey_trap)
    st.rerun()

payload = st.text_area("Flux d'entrée (Analyse de phase temps réel) :", height=200)

if st.button("AUDITER LE FLUX"):
    k, ctx, status = sentinel.analyze_autonomous(payload)
    
    if status == "CRITICAL":
        st.error(f"CRITICAL ANOMALY DETECTED | K-MASS: {k:.4f}")
        st.rerun()
    else:
        st.success(f"STABLE FLOW | CONTEXT: {ctx} | K-MASS: {k:.4f}")
        

# Historique local de session pour la démo
if 'history' not in st.session_state: st.session_state.history = []
if payload: st.session_state.history.append(sentinel.analyze_autonomous(payload)[0])

st.subheader("📈 Vecteur de Stabilité")
fig = go.Figure(go.Scatter(y=st.session_state.history[-50:], mode='lines+markers', line=dict(color='#00ff41')))
fig.update_layout(paper_bgcolor="black", plot_bgcolor="black")
st.plotly_chart(fig, use_container_width=True)
