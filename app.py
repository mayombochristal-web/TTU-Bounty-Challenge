import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
from datetime import datetime

# --- MOTEUR DE PERSISTANCE SÉCURISÉ (DATABASE VERSIONING) ---
DB_VERSION = "8.3" # Changer ce numéro force la réinitialisation de la structure

def init_db():
    # Si la version change ou si la DB n'existe pas, on initialise
    if 'db_memory' not in st.session_state or st.session_state.get('db_ver') != DB_VERSION:
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        c = conn.cursor()
        # Suppression au cas où pour éviter les conflits de colonnes
        c.execute('DROP TABLE IF EXISTS attackers')
        c.execute('DROP TABLE IF EXISTS audit_logs')
        # Création avec les 7 colonnes strictes
        c.execute('CREATE TABLE attackers (ip TEXT PRIMARY KEY, pseudo TEXT, depth INTEGER, last_seen TEXT)')
        c.execute('CREATE TABLE audit_logs (timestamp TEXT, ip TEXT, pseudo TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)')
        st.session_state.db_memory = conn
        st.session_state.db_ver = DB_VERSION
        if 'chart_data' not in st.session_state:
            st.session_state.chart_data = []

init_db()

def get_conn():
    return st.session_state.db_memory

# --- SYSTÈME D'IDENTIFICATION ---
if 'user_pseudo' not in st.session_state:
    st.markdown("""
        <div style="background-color: #0d1117; border: 2px solid #00ff41; padding: 30px; border-radius: 15px; text-align: center;">
            <h1 style='color: #00ff41;'>🔐 ACCÈS TTU-MC3 SÉCURITÉ</h1>
            <p style='color: #8b949e;'>Initialisation du profil d'expertise v8.3</p>
        </div>
    """, unsafe_allow_html=True)
    
    pseudo = st.text_input("NOM DE L'OPÉRATEUR / SIGNATURE HACKER :", key="init_pseudo")
    if st.button("ACTIVER LA SESSION"):
        if len(pseudo) >= 2:
            st.session_state.user_pseudo = pseudo
            st.rerun()
        else:
            st.error("Pseudo requis.")
    st.stop()

# --- CLASSE SENTINEL ---
class AbsoluteSentinel:
    def __init__(self, ip="127.0.0.1", pseudo="Unknown"):
        self.ip = ip
        self.pseudo = pseudo
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
        # Insertion garantie à 7 colonnes
        c.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (ts, self.ip, self.pseudo, ctx, k, status, payload[:100]))
        st.session_state.chart_data.append(k)
        if depth_up > 0:
            self.depth += depth_up
            c.execute("INSERT OR REPLACE INTO attackers VALUES (?, ?, ?, ?)", 
                      (self.ip, self.pseudo, self.depth, ts))
        conn.commit()

    def analyze_frequency(self, text):
        if len(text) < 2: return 1.0
        chars = pd.Series(list(text)).value_counts(normalize=True)
        zipf_ideal = np.array([1/i for i in range(1, len(chars)+1)])
        zipf_ideal /= zipf_ideal.sum()
        return np.linalg.norm(chars.values - zipf_ideal) + 0.1

    def process_flux(self, payload):
        if not payload: return 0.0, "NONE", "STABLE"
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "WHERE", "FROM", "SCRIPT"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        ctx = "CODE/INJECTION" if (has_sql or has_symbols) else "HUMAN_PROSE"
        sens = (6.0 + self.depth) if ctx == "CODE/INJECTION" else 0.4 
        symbols_count = sum(45.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.4 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        k_mass = round(float(k_mass), 4)
        status = "CRITICAL" if (k_mass > 1.0 or (has_sql and k_mass > 0.3)) else "STABLE"
        self.log_and_update(ctx, k_mass, status, payload, depth_up=(1 if status == "CRITICAL" else 0))
        return k_mass, ctx, status

# --- UI CONFIG ---
st.set_page_config(page_title="TTU-MC3 SÉCURITÉ", page_icon="🫆", layout="wide")
user_ip = "127.0.0.1" # Simulation IP
sentinel = AbsoluteSentinel(ip=user_ip, pseudo=st.session_state.user_pseudo)

# --- LE LABYRINTHE ---
if sentinel.depth > 0:
    st.markdown(f"<h1 style='color: #ff4b4b; text-align: center;'>🌀 LABYRINTHE NIVEAU {sentinel.depth}</h1>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    with col_l:
        choice = st.radio("Destin de l'Opérateur :", ["Aveu technique (Purge)", "Assaut Abyssal (Injection)"])
        if choice == "Aveu technique (Purge)":
            testimony = st.text_area("Expliquez l'échec de votre attaque (50 chars) :")
            if st.button("PURGER LA SIGNATURE"):
                if len(testimony) >= 50:
                    get_conn().execute("DELETE FROM attackers WHERE ip=?", (user_ip,))
                    st.rerun()
        else:
            p = st.text_area("Injection de force :")
            if st.button("LANCER L'ASSAUT"):
                sentinel.process_flux(p)
                st.rerun()
    with col_r:
        if st.session_state.chart_data:
            fig = go.Figure(go.Scatter(y=st.session_state.chart_data, line=dict(color='#ff4b4b', width=3, dash='dot')))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ff4b4b"), height=300)
            st.plotly_chart(fig, use_container_width=True)
    st.stop()

# --- SURFACE ---
st.title(f"🫆 TTU-MC3 : Abyss Engine")
c1, c2, c3 = st.columns(3)
c1.metric("OPÉRATEUR", st.session_state.user_pseudo)
c2.metric("IP", user_ip)
c3.metric("ABYSS DEPTH", sentinel.depth)

st.divider()

col_in, col_viz = st.columns([1, 1.2])
with col_in:
    payload = st.text_area("Audit de flux...", height=150)
    if st.button("ANALYSER"):
        k, ctx, stat = sentinel.process_flux(payload)
        if stat == "CRITICAL": st.rerun()
        else: st.success(f"STABLE (K-Mass: {k})")

with col_viz:
    if st.session_state.chart_data:
        fig = go.Figure(go.Scatter(y=st.session_state.chart_data, mode='lines+markers', line=dict(color='#00ff41')))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#00ff41"), height=300)
        st.plotly_chart(fig, use_container_width=True)

# --- RAPPORT D'EXPERTISE ---
st.divider()
st.subheader("📊 Rapport d'Expertise Détaillé")
if st.button("GÉNÉRER LE RAPPORT CSV"):
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", get_conn())
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 TÉLÉCHARGER EXPERTISE.CSV", csv, f"Expertise_TTU_{st.session_state.user_pseudo}.csv", "text/csv")
