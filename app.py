import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
from datetime import datetime
import os
import socket

# --- MOTEUR DE PERSISTANCE RÉEL (DISQUE) ---
DB_FILE = "ttu_security_bastion.db"

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attackers 
                 (ip TEXT PRIMARY KEY, pseudo TEXT, depth INTEGER, last_seen TEXT, total_kmass REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                 (timestamp TEXT, ip TEXT, pseudo TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)''')
    conn.commit()
    return conn

# --- DÉTECTION DE L'IP RÉELLE ---
def get_local_ip():
    try:
        # Connexion factice pour identifier l'interface réseau active
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Initialisation
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = init_db()
    if 'chart_data' not in st.session_state:
        st.session_state.chart_data = []

def get_conn():
    return st.session_state.db_conn

user_ip = get_local_ip()

# --- UI CONFIG ---
st.set_page_config(page_title="TTU-MC3 : Sécurité", page_icon="🏰", layout="wide")

# --- SYSTÈME D'IDENTIFICATION ---
if 'user_pseudo' not in st.session_state:
    st.markdown(f"""
        <div style="background-color: #0d1117; border: 2px solid #00ff41; padding: 30px; border-radius: 15px; text-align: center;">
            <h1 style='color: #00ff41;'>🔐 ACCÈS TTU-MC3 : SÉCURITÉ</h1>
            <p style='color: #8b949e;'>Terminal détecté sur l'IP : <b>{user_ip}</b></p>
        </div>
    """, unsafe_allow_html=True)
    
    pseudo = st.text_input("SIGNATURE DE L'OPÉRATEUR :", key="init_pseudo", placeholder="Entrez votre pseudo...")
    if st.button("ACTIVER LA SESSION"):
        if len(pseudo) >= 2:
            st.session_state.user_pseudo = pseudo
            st.rerun()
        else:
            st.error("Pseudo requis.")
    st.stop()

# --- CLASSE SENTINEL ---
class AbsoluteSentinel:
    def __init__(self, ip, pseudo):
        self.ip = ip
        self.pseudo = pseudo
        self.depth, self.total_k = self.load_status()

    def load_status(self):
        c = get_conn().cursor()
        c.execute("SELECT depth, total_kmass FROM attackers WHERE ip=?", (self.ip,))
        res = c.fetchone()
        return (res[0], res[1]) if res else (0, 0.0)

    def log_and_update(self, ctx, k, status, payload, depth_up=0):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (ts, self.ip, self.pseudo, ctx, k, status, payload[:200]))
        st.session_state.chart_data.append(k)
        new_depth = self.depth + depth_up
        new_total_k = self.total_k + k
        c.execute("INSERT OR REPLACE INTO attackers VALUES (?, ?, ?, ?, ?)", 
                  (self.ip, self.pseudo, new_depth, ts, new_total_k))
        conn.commit()

    def analyze_frequency(self, text):
        if len(text) < 2: return 1.0
        chars = pd.Series(list(text)).value_counts(normalize=True)
        zipf_ideal = np.array([1/i for i in range(1, len(chars)+1)])
        zipf_ideal /= zipf_ideal.sum()
        return np.linalg.norm(chars.values - zipf_ideal) + 0.1

    def process_flux(self, payload):
        if not payload: return 0.0, "NONE", "STABLE"
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "WHERE", "FROM", "SCRIPT", "ALERT"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        ctx = "CODE/INJECTION" if (has_sql or has_symbols) else "HUMAN_PROSE"
        sens = (7.0 + (self.depth * 2.5)) if ctx == "CODE/INJECTION" else 0.4 
        symbols_count = sum(50.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.5 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        k_mass = round(float(k_mass), 4)
        status = "CRITICAL" if (k_mass > 1.2 or (has_sql and k_mass > 0.4)) else "STABLE"
        self.log_and_update(ctx, k_mass, status, payload, depth_up=(1 if status == "CRITICAL" else 0))
        return k_mass, ctx, status

sentinel = AbsoluteSentinel(ip=user_ip, pseudo=st.session_state.user_pseudo)

# --- LOGIQUE LABYRINTHE ---
if sentinel.depth > 0:
    st.markdown(f"<h1 style='color: #ff4b4b; text-align: center;'>🌀 LABYRINTHE NIVEAU {sentinel.depth}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: grey;'>Terminal [{user_ip}] sous verrouillage.</p>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("💀 Négociation de sortie")
        suggested = "Je reconnais avoir testé les limites du système indûment." if sentinel.depth == 1 else "Signature entropique instable. Requête de réinitialisation."
        st.code(suggested, language="text")
        testimony = st.text_area("Plaidoyer (Min. 30 chars) :")
        if st.button("🤝 SOUMETTRE"):
            if len(testimony) >= 30:
                c = get_conn().cursor()
                c.execute("UPDATE attackers SET depth=? WHERE ip=?", (max(0, sentinel.depth - 1), user_ip))
                get_conn().commit()
                st.success("Rémission en cours...")
                time.sleep(1)
                st.rerun()
    with col_r:
        st.metric("SCORE DE MENACE", f"{round(sentinel.total_k, 2)} K-Mass")
    st.stop()

# --- SURFACE ---
st.title("🛡️ TTU-MC3 : SÉCURITÉ")
st.divider()

m1, m2, m3 = st.columns(3)
m1.metric("OPÉRATEUR", st.session_state.user_pseudo)
m2.metric("IP DÉTECTÉE", user_ip)
m3.metric("BAN DEPTH", sentinel.depth)

col_in, col_viz = st.columns([1, 1.2])
with col_in:
    payload = st.text_area("Audit de Flux...", height=150)
    if st.button("ANALYSER"):
        k, ctx, stat = sentinel.process_flux(payload)
        if stat == "CRITICAL": st.rerun()
        else: st.success(f"STABLE : K-Mass {k}")

with col_viz:
    if st.session_state.chart_data:
        fig = go.Figure(go.Scatter(y=st.session_state.chart_data, mode='lines+markers', line=dict(color='#00ff41')))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#00ff41"), height=300)
        st.plotly_chart(fig, use_container_width=True)

if st.button("GÉNÉRER LE RAPPORT"):
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", get_conn())
    st.dataframe(df)
