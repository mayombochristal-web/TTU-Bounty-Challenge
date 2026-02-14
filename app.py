import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
import io
from datetime import datetime

# --- MOTEUR DE BASE DE DONNÉES SÉCURISÉ ---
DB_NAME = 'sentinel_fortress.db'

def run_query(query, params=(), fetch=False, commit=False):
    """Gère les connexions de manière isolée pour éviter les OperationalError"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=20)
    conn.execute('PRAGMA journal_mode=WAL;') # Mode haute performance
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetch:
            return cursor.fetchall()
    finally:
        conn.close()

def init_db():
    run_query('''CREATE TABLE IF NOT EXISTS attackers 
                 (ip TEXT PRIMARY KEY, depth INTEGER, last_seen TIMESTAMP)''', commit=True)
    run_query('''CREATE TABLE IF NOT EXISTS audit_logs 
                 (timestamp TEXT, ip TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)''', commit=True)

init_db()

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="TTU-Shield v6.2", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #030507; color: #00ff41; font-family: 'Consolas', monospace; }
    .stMetric { background-color: #0a0e14; border: 1px solid #00ff41; padding: 15px; border-radius: 10px; }
    .stTextArea textarea { background-color: #05070a; color: #00ff41; border: 1px solid #00ff41; }
    </style>
    """, unsafe_allow_html=True)

class AbsoluteSentinel:
    def __init__(self, ip="127.0.0.1"):
        self.ip = ip
        self.depth = self.load_depth()

    def load_depth(self):
        res = run_query("SELECT depth FROM attackers WHERE ip=?", (self.ip,), fetch=True)
        return res[0][0] if res else 0

    def log_event(self, ctx, k, status, payload):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_query("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)", 
                  (ts, self.ip, ctx, k, status, payload[:100]), commit=True)

    def analyze_frequency(self, text):
        if len(text) < 2: return 1.0
        chars = pd.Series(list(text)).value_counts(normalize=True)
        zipf_ideal = np.array([1/i for i in range(1, len(chars)+1)])
        zipf_ideal /= zipf_ideal.sum()
        return np.linalg.norm(chars.values - zipf_ideal) + 0.1

    def process_flux(self, payload):
        if not payload: return 0.0, "NONE", "STABLE", "Attente de données..."
        
        # 1. DÉTECTION DE CONTEXTE RENFORCÉE
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "SCRIPT", "ALERT"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        
        ctx = "CODE/INJECTION" if (has_sql or has_symbols) else "HUMAN_PROSE"
        sens = 5.0 if ctx == "CODE/INJECTION" else 0.5

        # 2. CALCUL K-MASS (Division Logarithmique anti-dilution)
        symbols_count = sum(40.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.5 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        
        # 3. ÉTABLISSEMENT DU STATUT & PERSISTANCE SÉCURISÉE
        status = "STABLE"
        reason = "Vecteur sain. Intégrité confirmée."
        
        if k_mass > 1.2 or (has_sql and k_mass > 0.5):
            status = "CRITICAL"
            reason = "Rupture de phase détectée. Payload malveillant bloqué."
            self.depth += 1
            run_query("INSERT OR REPLACE INTO attackers VALUES (?, ?, ?)", 
                      (self.ip, self.depth, datetime.now()), commit=True)
        
        self.log_event(ctx, round(k_mass, 4), status, payload)
        return round(k_mass, 4), ctx, status, reason

# --- UI INTERFACE ---
sentinel = AbsoluteSentinel()

st.title("🛡️ TTU-Shield v6.2 : Fortress-Stable")

# --- ÉCRAN DU LABYRINTHE ---
if sentinel.depth > 0:
    st.markdown(f"### 🌀 LABYRINTHE NIVEAU {sentinel.depth} ACTIVÉ")
    st.error("Signature IP bannie par le Sentinel.")
    if st.button("DEMO: RESET IP & SORTIR"):
        run_query("DELETE FROM attackers WHERE ip=?", (sentinel.ip,), commit=True)
        st.rerun()
    st.stop()

m1, m2, m3 = st.columns(3)
m1.metric("SHIELD ENGINE", "v6.2")
m2.metric("THREAD PROTECTION", "ACTIVE")
m3.metric("DB MODE", "WAL (STABLE)")

st.divider()

col_in, col_viz = st.columns([1, 1.2])

with col_in:
    st.subheader("⌨️ Analyseur de Flux")
    payload = st.text_area("Entrez la donnée à auditer :", height=150)
    if st.button("AUDITER LE VECTEUR"):
        k, ctx, stat, reason = sentinel.process_flux(payload)
        if stat == "CRITICAL":
            st.error(f"DÉTECTION : {reason} (K-Mass: {k})")
            time.sleep(1)
            st.rerun()
        else:
            st.success(f"VALIDE : {reason} (K-Mass: {k})")

with col_viz:
    st.subheader("📊 Vibration de Phase")
    # Simulation de stabilité graphique
    st.line_chart(np.random.randn(20, 1) / 10)

# --- SECTION EXPORT CSV ---
st.divider()
st.subheader("📊 Audit & Exportation")
if st.button("🔄 GÉNÉRER / ACTUALISER LE RAPPORT"):
    res = run_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", fetch=True)
    if res:
        df = pd.DataFrame(res, columns=["Timestamp", "IP", "Context", "K-Mass", "Status", "Payload"])
        st.dataframe(df.head(10))
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 TÉLÉCHARGER LE CSV COMPLET", data=csv, 
                           file_name=f"audit_sentinel_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')
    else:
        st.write("Aucun log disponible pour le moment.")
