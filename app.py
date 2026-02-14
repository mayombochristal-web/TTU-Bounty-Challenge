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

# --- DATABASE PERSISTENCE ---
def init_db():
    conn = sqlite3.connect('sentinel_fortress.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attackers 
                 (ip TEXT PRIMARY KEY, depth INTEGER, last_seen TIMESTAMP)''')
    # Table d'audit pour l'export CSV
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                 (timestamp TEXT, ip TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)''')
    conn.commit()
    return conn

db_conn = init_db()

# --- APP CONFIGURATION ---
st.set_page_config(page_title="TTU-Shield v6.0", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #030507; color: #00ff41; font-family: 'Consolas', monospace; }
    .stMetric { background-color: #0a0e14; border: 1px solid #00ff41; padding: 15px; border-radius: 10px; }
    .status-alert { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; border: 2px solid; }
    </style>
    """, unsafe_allow_html=True)

class AbsoluteSentinel:
    def __init__(self, ip="127.0.0.1"):
        self.ip = ip
        self.load_status()

    def load_status(self):
        c = db_conn.cursor()
        c.execute("SELECT depth FROM attackers WHERE ip=?", (self.ip,))
        res = c.fetchone()
        self.depth = res[0] if res else 0

    def log_event(self, ctx, k, status, payload):
        c = db_conn.cursor()
        c.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.ip, ctx, k, status, payload[:50]))
        db_conn.commit()

    def analyze_frequency(self, text):
        if len(text) < 2: return 1.0
        chars = pd.Series(list(text)).value_counts(normalize=True)
        zipf_ideal = np.array([1/i for i in range(1, len(chars)+1)])
        zipf_ideal /= zipf_ideal.sum()
        return np.linalg.norm(chars.values - zipf_ideal) + 0.1

    def process_flux(self, payload):
        if not payload: return 0.0, "NONE", "STABLE", "En attente..."
        
        # 1. DÉTECTION DE CONTEXTE RENFORCÉE (Anti-Camouflage)
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "SCRIPT", "ALERT"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        
        if has_sql or has_symbols:
            ctx = "CODE/INJECTION"
            sens = 5.0 # Sensibilité extrême
        elif payload.isdigit():
            ctx = "NUMERIC"
            sens = 3.0
        else:
            ctx = "HUMAN_PROSE"
            sens = 0.5

        # 2. CALCUL K-MASS V6 (Correction de la faille de dilution)
        symbols_count = sum(40.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.5 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        
        # Utilisation d'une division logarithmique pour empêcher la dilution par la longueur
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        
        # 3. ÉTABLISSEMENT DU STATUT
        if k_mass > 1.2 or (has_sql and k_mass > 0.5):
            status = "CRITICAL"
            reason = "Rupture de phase détectée. Contenu malveillant identifié sous camouflage."
            self.depth += 1
            c = db_conn.cursor()
            c.execute("INSERT OR REPLACE INTO attackers VALUES (?, ?, ?)", (self.ip, self.depth, datetime.now()))
            db_conn.commit()
        else:
            status = "STABLE"
            reason = "Vecteur sain. Intégrité confirmée."
        
        self.log_event(ctx, round(k_mass, 4), status, payload)
        return round(k_mass, 4), ctx, status, reason

# --- UI INTERFACE ---
sentinel = AbsoluteSentinel()

st.title("🛡️ TTU-Shield v6.0 : Absolute-Zero")
st.write(f"Monitor IP: `{sentinel.ip}` | Database Persistence: `ACTIVE`")

# --- GESTION DU LABYRINTHE ---
if sentinel.depth > 0:
    st.markdown(f"<div class='status-alert' style='border-color: #ff4b4b; color: #ff4b4b;'>🌀 LABYRINTHE NIVEAU {sentinel.depth} ACTIVÉ</div>", unsafe_allow_html=True)
    st.error("Votre signature IP a été bannie suite à une détection de 'Camouflage Sémantique'.")
    
    if st.button("RÉINITIALISER (DEMO ONLY)"):
        c = db_conn.cursor()
        c.execute("DELETE FROM attackers WHERE ip=?", (sentinel.ip,))
        db_conn.commit()
        st.rerun()
    st.stop()

# --- INTERFACE DE SURFACE ---
m1, m2, m3 = st.columns(3)
m1.metric("SHIELD ENGINE", "v6.0-Alpha")
m2.metric("THREAT DETECTION", "REAL-TIME")
m3.metric("LOG PERSISTENCE", "SQLITE3")

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
            st.write(f"Contexte: `{ctx}`")

with col_viz:
    st.subheader("🔮 Topologie de Phase")
    # Simulation graphique pour l'UX
    chart_data = pd.DataFrame(np.random.randn(20, 1) / 10, columns=['Vibration'])
    st.line_chart(chart_data)

# --- SECTION EXPORT CSV ---
st.divider()
st.subheader("📊 Administration & Audit")
if st.button("GÉNÉRER LE RAPPORT D'AUDIT (CSV)"):
    c = db_conn.cursor()
    df = pd.read_sql_query("SELECT * FROM audit_logs", db_conn)
    
    # Conversion en CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger sentinel_audit.csv",
        data=csv,
        file_name=f"sentinel_audit_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )
    st.dataframe(df.tail(10))
