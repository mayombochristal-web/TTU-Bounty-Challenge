import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
from datetime import datetime

# --- INITIALISATION DE LA BASE EN MÉMOIRE ---
if 'db_memory' not in st.session_state:
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE attackers (ip TEXT PRIMARY KEY, depth INTEGER, last_seen TEXT)')
    c.execute('CREATE TABLE audit_logs (timestamp TEXT, ip TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)')
    st.session_state.db_memory = conn
    st.session_state.chart_data = [] # Pour un rafraîchissement fluide du graphique

def get_conn():
    return st.session_state.db_memory

# --- CLASSE SENTINEL OMNISCIENTE ---
class AbsoluteSentinel:
    def __init__(self, ip="127.0.0.1"):
        self.ip = ip
        self.depth = self.load_depth()

    def load_depth(self):
        c = get_conn().cursor()
        c.execute("SELECT depth FROM attackers WHERE ip=?", (self.ip,))
        res = c.fetchone()
        return res[0] if res else 0

    def log_and_update(self, ctx, k, status, payload, depth_up=0):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)", 
                  (ts, self.ip, ctx, k, status, payload[:100]))
        if depth_up > 0:
            self.depth += depth_up
            c.execute("INSERT OR REPLACE INTO attackers VALUES (?, ?, ?)", (self.ip, self.depth, ts))
        conn.commit()
        # Mise à jour immédiate du graphique
        st.session_state.chart_data.append(k)

    def analyze_frequency(self, text):
        if len(text) < 2: return 1.0
        chars = pd.Series(list(text)).value_counts(normalize=True)
        zipf_ideal = np.array([1/i for i in range(1, len(chars)+1)])
        zipf_ideal /= zipf_ideal.sum()
        return np.linalg.norm(chars.values - zipf_ideal) + 0.1

    def process_flux(self, payload):
        if not payload: return 0.0, "NONE", "STABLE"
        
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "WHERE", "FROM"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        
        ctx = "CODE/INJECTION" if (has_sql or has_symbols) else "HUMAN_PROSE"
        sens = 6.0 if ctx == "CODE/INJECTION" else 0.4 

        symbols_count = sum(45.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.4 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        k_mass = round(float(k_mass), 4)
        
        status = "CRITICAL" if (k_mass > 1.0 or (has_sql and k_mass > 0.3)) else "STABLE"
        depth_to_add = 1 if status == "CRITICAL" else 0
        
        self.log_and_update(ctx, k_mass, status, payload, depth_up=depth_to_add)
        return k_mass, ctx, status

# --- UI CONFIGURATION ---
st.set_page_config(page_title="TTU-MC3 SÉCURITÉ", page_icon="🫆", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #030507; color: #00ff41; font-family: 'Courier New', monospace; }
    .stMetric { background-color: #0d1117; border: 1px solid #00ff41; padding: 15px; border-radius: 10px; }
    .stTextArea textarea { background-color: #07080a; color: #00ff41; border: 1px solid #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

sentinel = AbsoluteSentinel()

st.title("🫆 TTU-MC3 SÉCURITÉ : Omniscient Engine")

# --- LE LABYRINTHE (L'expérience Hacker) ---
if sentinel.depth > 0:
    st.markdown(f"<h1 style='color: #ff4b4b; text-align: center;'>🌀 LABYRINTHE NIVEAU {sentinel.depth} ACTIVÉ</h1>", unsafe_allow_html=True)
    st.error("DÉTECTION DE PHASE : Votre intention a été jugée hostile par l'algorithme TTU-MC3.")
    
    
    
    col_lab1, col_lab2 = st.columns(2)
    
    with col_lab1:
        st.subheader("🔓 Aveu de Défaite")
        st.write("Le Sentinel ne libère pas les signatures sans un témoignage de l'efficacité du système.")
        testimony = st.text_area("Expliquez comment l'algorithme a détecté votre injection et pourquoi votre attaque a échoué (min. 50 caractères) :", height=200)
        
        if st.button("SOUMETTRE MON AVEU"):
            if len(testimony) >= 50:
                c = get_conn().cursor()
                c.execute("DELETE FROM attackers WHERE ip=?", (sentinel.ip,))
                st.success("✅ Aveu enregistré. Réalignement de la signature IP...")
                time.sleep(2)
                st.rerun()
            else:
                st.warning("⚠️ Témoignage insuffisant. Le labyrinthe reste scellé.")
                
    with col_lab2:
        st.subheader("📉 Signature de Rupture")
        if st.session_state.chart_data:
            st.line_chart(st.session_state.chart_data, color="#ff4b4b")
        st.info("Visualisation de l'anomalie de phase ayant causé le verrouillage.")
    st.stop()

# --- INTERFACE DE SURFACE ---
m1, m2, m3 = st.columns(3)
m1.metric("STATUS", "ACTIVE WATCH")
m2.metric("THREAT LEVEL", "NORMAL")
m3.metric("K-MASS BASELINE", "0.41")

st.divider()

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("⌨️ Input Stream Audit")
    payload = st.text_area("Injection de données pour analyse de phase...", height=180, placeholder="Texte humain ou script malveillant...")
    
    if st.button("AUDITER LE VECTEUR"):
        k, ctx, stat = sentinel.process_flux(payload)
        if stat == "CRITICAL":
            st.error(f"☢️ CRITICAL ANOMALY : K-Mass {k}")
            time.sleep(1)
            st.rerun()
        else:
            st.success(f"✔️ FLOW STABLE : K-Mass {k}")
            st.write(f"Contexte détecté : **{ctx}**")

with col2:
    st.subheader("🔮 Métriques de Phase en Temps Réel")
    if st.session_state.chart_data:
        # Utilisation de Plotly pour un graphique plus "pro"
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=st.session_state.chart_data, mode='lines+markers', line=dict(color='#00ff41', width=3)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                          font=dict(color="#00ff41"), margin=dict(l=0,r=0,b=0,t=0), height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("En attente de flux de données pour génération topologique...")

# --- ADMINISTRATION ---
st.divider()
if st.button("📊 GÉNÉRER RAPPORT D'AUDIT COMPLET (CSV)"):
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", get_conn())
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 EXPORTER LES PREUVES", csv, "audit_ttu_mc3.csv", "text/csv")
