import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
import os
from datetime import datetime

# --- MOTEUR DE BASE DE DONNÉES SÉCURISÉ (ZERO-LOCK) ---
DB_NAME = 'sentinel_fortress.db'

def init_db():
    """Initialisation avec gestion d'erreurs robuste"""
    with sqlite3.connect(DB_NAME, check_same_thread=False, timeout=30) as conn:
        conn.execute('PRAGMA journal_mode=WAL;') # Mode de journalisation pour accès concurrents
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS attackers 
                     (ip TEXT PRIMARY KEY, depth INTEGER, last_seen TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                     (timestamp TEXT, ip TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)''')
        conn.commit()

init_db()

class AbsoluteSentinel:
    def __init__(self, ip="127.0.0.1"):
        self.ip = ip
        self.depth = self.load_depth()

    def load_depth(self):
        with sqlite3.connect(DB_NAME, check_same_thread=False, timeout=30) as conn:
            c = conn.cursor()
            c.execute("SELECT depth FROM attackers WHERE ip=?", (self.ip,))
            res = c.fetchone()
            return res[0] if res else 0

    def log_and_update(self, ctx, k, status, payload, depth_up=0):
        """Regroupe les écritures en une seule transaction pour éviter les verrous"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_NAME, check_same_thread=False, timeout=30) as conn:
            c = conn.cursor()
            # 1. Log l'événement
            c.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)", 
                      (ts, self.ip, ctx, k, status, payload[:100]))
            # 2. Update profondeur si nécessaire
            if depth_up > 0:
                self.depth += depth_up
                c.execute("INSERT OR REPLACE INTO attackers VALUES (?, ?, ?)", 
                          (self.ip, self.depth, ts))
            conn.commit()

    def analyze_frequency(self, text):
        if len(text) < 2: return 1.0
        chars = pd.Series(list(text)).value_counts(normalize=True)
        zipf_ideal = np.array([1/i for i in range(1, len(chars)+1)])
        zipf_ideal /= zipf_ideal.sum()
        return np.linalg.norm(chars.values - zipf_ideal) + 0.1

    def process_flux(self, payload):
        if not payload: return 0.0, "NONE", "STABLE", "En attente..."
        
        # DÉTECTION DE CONTEXTE RENFORCÉE (Correctif faille dilution)
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "SCRIPT", "ALERT", "WHERE"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        
        ctx = "CODE/INJECTION" if (has_sql or has_symbols) else "HUMAN_PROSE"
        sens = 5.0 if ctx == "CODE/INJECTION" else 0.5

        # CALCUL K-MASS V6 (Logarithmique)
        symbols_count = sum(40.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.5 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        k_mass = round(float(k_mass), 4)
        
        status = "STABLE"
        reason = "Vecteur sain."
        depth_to_add = 0

        if k_mass > 1.1 or (has_sql and k_mass > 0.4):
            status = "CRITICAL"
            reason = "Rupture de phase : Tentative malveillante identifiée."
            depth_to_add = 1
        
        self.log_and_update(ctx, k_mass, status, payload, depth_up=depth_to_add)
        return k_mass, ctx, status, reason

# --- UI STREAMLIT ---
st.set_page_config(page_title="TTU-Shield v6.3", page_icon="🛡️", layout="wide")
sentinel = AbsoluteSentinel()

st.title("🛡️ TTU-Shield v6.3 : Zero-Lock Edition")

# --- GESTION DU LABYRINTHE ---
if sentinel.depth > 0:
    st.markdown(f"### 🌀 LABYRINTHE NIVEAU {sentinel.depth} ACTIVÉ")
    st.error("Votre IP a été bannie pour anomalie structurelle.")
    if st.button("DEMO: RESET IP"):
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("DELETE FROM attackers WHERE ip=?", (sentinel.ip,))
        st.rerun()
    st.stop()

# --- ANALYSEUR ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("⌨️ Input Stream")
    payload = st.text_area("Donnée à auditer :", height=150)
    if st.button("AUDITER LE VECTEUR"):
        k, ctx, stat, reason = sentinel.process_flux(payload)
        if stat == "CRITICAL":
            st.error(f"ALERTE : {reason} (K: {k})")
            time.sleep(1)
            st.rerun()
        else:
            st.success(f"VALIDE : {reason} (K: {k})")

with col2:
    st.subheader("📊 Vibration de Phase")
    st.line_chart(np.random.randn(20, 1) / 10)

# --- AUDIT & EXPORT ---
st.divider()
st.subheader("📊 Audit & Exportation CSV")
if st.button("🔄 ACTUALISER LES LOGS"):
    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", conn)
        st.dataframe(df.head(15))
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger le rapport CSV",
            data=csv,
            file_name=f"audit_sentinel_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )
