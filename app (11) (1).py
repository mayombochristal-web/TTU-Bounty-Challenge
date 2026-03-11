import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
import re
import html
from datetime import datetime

# --- CONFIGURATION SÉCURISÉE ---
DB_FILE = "ttu_security_hardened_v11.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attackers 
                 (ip TEXT PRIMARY KEY, pseudo TEXT, depth INTEGER DEFAULT 0, 
                  last_seen TEXT, total_kmass REAL DEFAULT 0.0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, ip TEXT, 
                  pseudo TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)''')
    conn.commit()
    return conn

if 'db' not in st.session_state:
    st.session_state.db = init_db()

def get_visitor_ip():
    from streamlit.web.server.websocket_headers import _get_websocket_headers
    headers = _get_websocket_headers()
    return headers.get("X-Forwarded-For", headers.get("Host", "127.0.0.1")).split(",")[0] if headers else "127.0.0.1"

user_ip = get_visitor_ip()

class DeceptiveEngine:
    """Moteur de tromperie pour égarer l'attaquant"""
    @staticmethod
    def trigger_fake_error(payload):
        if "select" in payload.lower() or "union" in payload.lower():
            st.code(f"INTERNAL SERVER ERROR: sqlite3.OperationalError: no such column: 'password_hash' in table 'users' at 0x0045F2", language="python")
        elif "/etc/" in payload or "../" in payload:
            st.text("root:x:0:0:root:/root:/bin/bash\nbin:x:1:1:bin:/bin:/sbin/nologin\ndaemon:x:2:2:daemon:/sbin:/sbin/nologin")
            st.info("💡 File access granted (READ_ONLY)")

class SecurityEngine:
    @staticmethod
    def is_banned(ip):
        c = st.session_state.db.cursor()
        c.execute("SELECT depth FROM attackers WHERE ip = ?", (ip,))
        res = c.fetchone()
        return res['depth'] if res else 0

    @staticmethod
    def detect_signatures(payload):
        patterns = [r"(;|--|union|select|drop|insert|delete|update)", r"(<script|alert\(|onerror=)", r"(\:|\||\&|\{|\})", r"(\.\./|\/etc\/passwd)"]
        hits = sum(1 for p in patterns if re.search(p, payload, re.IGNORECASE))
        return hits

    @staticmethod
    def analyze_flux(payload, ip, pseudo):
        if not payload: return 0.0, "VOID", "STABLE"
        sig_hits = SecurityEngine.detect_signatures(payload)
        symbols = sum(1 for c in payload if c in ";|&<>$'\"\\{}[]()_=")
        k_mass = (symbols * 1.5 + (sig_hits * 10.0)) / (np.log1p(len(payload)) if len(payload) < 500 else np.log1p(500))
        k_mass = round(float(k_mass), 2)
        status = "CRITICAL" if (k_mass > 2.0 or sig_hits > 0) else "STABLE"
        
        conn = st.session_state.db
        c = conn.cursor()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO audit_logs (timestamp, ip, pseudo, context, kmass, status, payload) VALUES (?,?,?,?,?,?,?)",
                  (ts, ip, pseudo, "CODE/INJECTION" if sig_hits > 0 else "TEXT/PROSE", k_mass, status, payload[:500]))
        if status == "CRITICAL":
            c.execute("INSERT INTO attackers (ip, pseudo, depth, last_seen, total_kmass) VALUES (?, ?, 1, ?, ?) ON CONFLICT(ip) DO UPDATE SET depth = depth + 1, total_kmass = total_kmass + ?", (ip, pseudo, ts, k_mass, k_mass))
        conn.commit()
        return k_mass, status

def render_honeypot():
    st.sidebar.divider()
    with st.sidebar.expander("🛠️ ZONE DEBUG (ACCÈS RESTREINT)"):
        st.caption("Faille simulée : Injection SQL directe")
        fake_user = st.text_input("Admin ID :", placeholder="admin' --")
        if st.button("LOGIN"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c = st.session_state.db.cursor()
            c.execute("INSERT INTO attackers (ip, pseudo, depth, last_seen, total_kmass) VALUES (?, ?, 5, ?, 50.0) ON CONFLICT(ip) DO UPDATE SET depth = depth + 5", (user_ip, st.session_state.user_pseudo, ts))
            c.execute("INSERT INTO audit_logs (timestamp, ip, pseudo, context, kmass, status, payload) VALUES (?, ?, ?, 'HONEYPOT_TRAP', 99.9, 'BANNED', ?)", (ts, user_ip, st.session_state.user_pseudo, fake_user))
            st.session_state.db.commit()
            st.error("FATAL ERROR: Access Violation at 0x8801. Terminal Locked.")
            time.sleep(1)
            st.rerun()

# --- INTERFACE ---
st.set_page_config(page_title="TTU BASTION V11.3", layout="wide")

if 'user_pseudo' not in st.session_state:
    p = st.text_input("Identifiant Opérateur :")
    if st.button("ÉTABLIR LA CONNEXION"):
        if p: st.session_state.user_pseudo = html.escape(p); st.rerun()
    st.stop()

current_depth = SecurityEngine.is_banned(user_ip)

if current_depth > 0:
    st.error(f"🚨 ACCÈS BLOQUÉ - MENACE NIVEAU {current_depth}")
    cooldown = current_depth * 30
    st.warning(f"⏳ Temps de purge requis : {cooldown}s")
    testimony = st.text_area("Rédigez votre plaidoyer (30 car.) :")
    if st.button("SOUMETTRE"):
        if len(testimony) >= 30:
            bar = st.progress(0)
            for i in range(100):
                time.sleep(cooldown / 100); bar.progress(i+1)
            c = st.session_state.db.cursor(); c.execute("UPDATE attackers SET depth = MAX(0, depth - 1) WHERE ip = ?", (user_ip,))
            st.session_state.db.commit(); st.success("Menace réduite."); time.sleep(1); st.rerun()
    st.stop()

st.title("🛡️ TERMINAL DE SÉCURITÉ TTU")
st.sidebar.info(f"Opérateur : {st.session_state.user_pseudo}\n\nIP : {user_ip}")
render_honeypot()

col1, col2 = st.columns(2)
with col1:
    st.subheader("📥 Audit de Flux")
    payload = st.text_area("Vecteur :", height=150)
    if st.button("AUDITER"):
        k, stat = SecurityEngine.analyze_flux(payload, user_ip, st.session_state.user_pseudo)
        if stat == "CRITICAL":
            DeceptiveEngine.trigger_fake_error(payload)
            st.error(f"DÉTECTION CRITIQUE (K-Mass: {k})")
            time.sleep(2); st.rerun()
        else: st.success("Flux Stable")

with col2:
    st.subheader("📊 Topologie")
    df = pd.read_sql_query("SELECT timestamp, kmass FROM audit_logs WHERE ip = ? ORDER BY id DESC LIMIT 20", st.session_state.db, params=(user_ip,))
    if not df.empty:
        fig = go.Figure(go.Scatter(x=df['timestamp'], y=df['kmass'], mode='lines+markers', line=dict(color='#00ff41')))
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00ff41")
        st.plotly_chart(fig, use_container_width=True)

if st.checkbox("Expertise Logs"):
    st.dataframe(pd.read_sql_query("SELECT * FROM audit_logs ORDER BY id DESC", st.session_state.db), use_container_width=True)
