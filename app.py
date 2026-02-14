import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import hashlib
import time
import sqlite3
import re
import io
from datetime import datetime

# --- DATABASE ENGINE (THREAD-SAFE) ---
def get_db_connection():
    # check_same_thread=False est crucial pour Streamlit
    conn = sqlite3.connect('sentinel_fortress.db', check_same_thread=False)
    # On force le mode WAL (Write-Ahead Logging) pour permettre lectures et écritures simultanées
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attackers 
                 (ip TEXT PRIMARY KEY, depth INTEGER, last_seen TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                 (timestamp TEXT, ip TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="TTU-Shield v6.1", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #030507; color: #00ff41; font-family: 'Consolas', monospace; }
    .stMetric { background-color: #0a0e14; border: 1px solid #00ff41; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

class AbsoluteSentinel:
    def __init__(self, ip="127.0.0.1"):
        self.ip = ip
        self.depth = self.load_depth()

    def load_depth(self):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT depth FROM attackers WHERE ip=?", (self.ip,))
        res = c.fetchone()
        conn.close()
        return res[0] if res else 0

    def log_event(self, ctx, k, status, payload):
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)",
                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.ip, ctx, k, status, payload[:100]))
            conn.commit()
        finally:
            conn.close()

    def analyze_frequency(self, text):
        if len(text) < 2: return 1.0
        chars = pd.Series(list(text)).value_counts(normalize=True)
        zipf_ideal = np.array([1/i for i in range(1, len(chars)+1)])
        zipf_ideal /= zipf_ideal.sum()
        return np.linalg.norm(chars.values - zipf_ideal) + 0.1

    def process_flux(self, payload):
        if not payload: return 0.0, "NONE", "STABLE", "En attente..."
        
        # 1. DÉTECTION DE CONTEXTE RENFORCÉE
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "SCRIPT", "ALERT"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        
        if has_sql or has_symbols:
            ctx = "CODE/INJECTION"
            sens = 5.0
        else:
            ctx = "HUMAN_PROSE"
            sens = 0.5

        # 2. CALCUL K-MASS (Division Logarithmique)
        symbols_count = sum(40.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.5 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        
        # 3. ÉTABLISSEMENT DU STATUT & PERSISTANCE
        if k_mass > 1.2 or (has_sql and k_mass > 0.5):
            status = "CRITICAL"
            reason = "Rupture de phase détectée. Payload malveillant bloqué."
            self.depth += 1
            # Mise à jour de la profondeur dans la DB
            conn = get_db_connection()
            try:
                conn.execute("INSERT OR REPLACE INTO attackers VALUES (?, ?, ?)", 
                             (self.ip, self.depth, datetime.now()))
                conn.commit()
            finally:
                conn.close()
        else:
            status = "STABLE"
            reason = "Vecteur sain. Intégrité confirmée."
        
        self.log_event(ctx, round(k_mass, 4), status, payload)
        return round(k_mass, 4), ctx, status, reason

# --- UI INTERFACE ---
sentinel = AbsoluteSentinel()

st.title("🛡️ TTU-Shield v6.1 : Absolute-Zero")

if sentinel.depth > 0:
    st.markdown(f"### 🌀 LABYRINTHE NIVEAU {sentinel.depth} ACTIVÉ")
    st.error("Signature IP bannie par le Sentinel.")
    if st.button("DEMO: RESET IP"):
        conn = get_db_connection()
        conn.execute("DELETE FROM attackers WHERE ip=?", (sentinel.ip,))
        conn.commit()
        conn.close()
        st.rerun()
    st.stop()

m1, m2, m3 = st.columns(3)
m1.metric("SHIELD ENGINE", "v6.1")
m2.metric("THREAT DETECTION", "REAL-TIME")
m3.metric("LOG PERSISTENCE", "SQLITE3 (WAL)")

st.divider()

col_in, col_viz = st.columns([1, 1.2])

with col_in:
    st.subheader("⌨️ Analyseur de Flux")
    payload = st.text_area("Entrez la donnée à auditer :", height=150)
    if st.button("AUDITER LE VECTEUR"):
        k, ctx, stat, reason = sentinel.process_flux(payload)
        if stat == "CRITICAL":
            st.error(f"DÉTECTION : {reason} (K-Mass: {k})")
            time.sleep(1.5)
            st.rerun()
        else:
            st.success(f"VALIDE : {reason} (K-Mass: {k})")

with col_viz:
    st.subheader("📊 Vibration de Phase")
    # Simulation graphique
    st.line_chart(np.random.randn(20, 1) / 10)

# --- SECTION ADMINISTRATION & EXPORT ---
st.divider()
st.subheader("📊 Administration & Audit")

col_adm1, col_adm2 = st.columns(2)

with col_adm1:
    if st.button("🔄 GÉNÉRER LE RAPPORT D'AUDIT"):
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", conn)
        conn.close()
        st.session_state.audit_df = df
        st.dataframe(df.head(10))

with col_adm2:
    if 'audit_df' in st.session_state:
        csv = st.session_state.audit_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 TÉLÉCHARGER CSV",
            data=csv,
            file_name=f"sentinel_audit_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime='text/csv',
        )
