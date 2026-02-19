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
    if headers:
        return headers.get("X-Forwarded-For", headers.get("Host", "127.0.0.1")).split(",")[0]
    return "127.0.0.1"

user_ip = get_visitor_ip()

class SecurityEngine:
    @staticmethod
    def is_banned(ip):
        c = st.session_state.db.cursor()
        c.execute("SELECT depth FROM attackers WHERE ip = ?", (ip,))
        res = c.fetchone()
        return res['depth'] if res else 0

    @staticmethod
    def sanitize(text):
        return html.escape(text)

    @staticmethod
    def detect_signatures(payload):
        patterns = [
            r"(;|--|union|select|drop|insert|delete|update)", 
            r"(<script|alert\(|onerror=)",                   
            r"(\:|\||\&|\{|\})",                             
            r"(\.\./|\/etc\/passwd|\/windows\/win\.ini)"      
        ]
        hits = 0
        for p in patterns:
            if re.search(p, payload, re.IGNORECASE):
                hits += 1
        return hits

    @staticmethod
    def analyze_flux(payload, ip, pseudo):
        if not payload: return 0.0, "VOID", "STABLE"
        sig_hits = SecurityEngine.detect_signatures(payload)
        symbols = sum(1 for c in payload if c in ";|&<>$'\"\\{}[]()_=")
        length_factor = np.log1p(len(payload)) if len(payload) < 500 else np.log1p(500)
        k_mass = (symbols * 1.5 + (sig_hits * 10.0)) / length_factor
        k_mass = round(float(k_mass), 2)
        
        status = "CRITICAL" if (k_mass > 2.0 or sig_hits > 0) else "STABLE"
        ctx = "CODE/INJECTION" if sig_hits > 0 else "TEXT/PROSE"
        
        conn = st.session_state.db
        c = conn.cursor()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute("INSERT INTO audit_logs (timestamp, ip, pseudo, context, kmass, status, payload) VALUES (?,?,?,?,?,?,?)",
                  (ts, ip, pseudo, ctx, k_mass, status, payload[:500]))
        
        if status == "CRITICAL":
            c.execute("""INSERT INTO attackers (ip, pseudo, depth, last_seen, total_kmass) 
                         VALUES (?, ?, 1, ?, ?) 
                         ON CONFLICT(ip) DO UPDATE SET 
                         depth = depth + 1, last_seen = ?, total_kmass = total_kmass + ?""",
                      (ip, pseudo, ts, k_mass, ts, k_mass))
        conn.commit()
        return k_mass, ctx, status

def render_honeypot():
    st.sidebar.divider()
    with st.sidebar.expander("🛠️ ZONE DEBUG (ACCÈS RESTREINT)"):
        st.caption("Faille simulée : Injection SQL directe")
        fake_user = st.text_input("Admin ID :", placeholder="ex: admin' --")
        fake_pass = st.text_input("Password :", type="password")
        
        if st.button("LOGIN"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = st.session_state.db
            c = conn.cursor()
            c.execute("""INSERT INTO attackers (ip, pseudo, depth, last_seen, total_kmass) 
                         VALUES (?, ?, 5, ?, 50.0) 
                         ON CONFLICT(ip) DO UPDATE SET 
                         depth = depth + 5, last_seen = ?, total_kmass = total_kmass + 50.0""",
                      (user_ip, st.session_state.user_pseudo, ts, ts))
            c.execute("""INSERT INTO audit_logs (timestamp, ip, pseudo, context, kmass, status, payload) 
                         VALUES (?, ?, ?, 'HONEYPOT_TRAP', 99.9, 'BANNED', ?)""",
                      (ts, user_ip, st.session_state.user_pseudo, f"Tentative d'accès Admin : {fake_user}"))
            conn.commit()
            st.error("DÉTECTION INTRUSION : Signalement envoyé.")
            time.sleep(1)
            st.rerun()

# --- CONFIG PAGE ---
st.set_page_config(page_title="TTU BASTION V11.2", layout="wide")

if 'user_pseudo' not in st.session_state:
    st.title("🔐 ACCÈS BASTION TTU-MC3")
    p = st.text_input("Identifiant Opérateur :")
    if st.button("ÉTABLIR LA CONNEXION"):
        if p: 
            st.session_state.user_pseudo = SecurityEngine.sanitize(p)
            st.rerun()
    st.stop()

# --- LOGIQUE DE BANNISSEMENT AVEC COOLDOWN ---
current_depth = SecurityEngine.is_banned(user_ip)

if current_depth > 0:
    st.error(f"🚨 ACCÈS BLOQUÉ - NIVEAU DE MENACE {current_depth}")
    
    # Calcul du Cooldown : 30 secondes par point de depth
    cooldown_target = current_depth * 30
    st.warning(f"Protocole de stabilisation actif. Attente requise : {cooldown_target} secondes.")
    
    

    testimony = st.text_area("Rédigez votre plaidoyer de rémission (30 car. min) :", height=150)
    
    # Le bouton ne s'active qu'après simulation du temps d'attente
    if st.button("🤝 SOUMETTRE LA RÉMISSION"):
        if len(testimony) >= 30:
            with st.spinner(f"Analyse cryptographique en cours... Veuillez patienter {cooldown_target}s"):
                # Simulation du Cooldown (bloque l'UI pour décourager l'attaquant)
                # Note: sleep(cooldown_target) peut être long, on peut simuler une barre de progression
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(cooldown_target / 100)
                    progress_bar.progress(i + 1)
                
                c = st.session_state.db.cursor()
                c.execute("UPDATE attackers SET depth = MAX(0, depth - 1) WHERE ip = ?", (user_ip,))
                st.session_state.db.commit()
                st.success("Rémission accordée. Niveau de menace réduit.")
                time.sleep(1)
                st.rerun()
        else:
            st.error("Plaidoyer insuffisant pour une purge entropique.")
    st.stop()

# --- DASHBOARD ---
st.title("🛡️ TERMINAL DE SÉCURITÉ TTU")
st.sidebar.info(f"Opérateur : {st.session_state.user_pseudo}\n\nIP : {user_ip}")
render_honeypot()

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("📥 Analyse de Flux")
    input_data = st.text_area("Vecteur à tester :", height=200)
    if st.button("LANCER L'AUDIT"):
        k, ctx, stat = SecurityEngine.analyze_flux(input_data, user_ip, st.session_state.user_pseudo)
        if stat == "CRITICAL":
            st.error(f"ALERTE : Menace détectée (K-Mass: {k})")
            time.sleep(1)
            st.rerun()
        else:
            st.success(f"Flux stable : {ctx}")

with col2:
    st.subheader("📊 État du Réseau")
    c = st.session_state.db.cursor()
    c.execute("SELECT timestamp, kmass FROM audit_logs WHERE ip = ? ORDER BY id DESC LIMIT 20", (user_ip,))
    history = c.fetchall()
    if history:
        df_hist = pd.DataFrame(history, columns=['Time', 'K-Mass'])
        fig = go.Figure(go.Scatter(x=df_hist['Time'], y=df_hist['K-Mass'], mode='lines+markers', line=dict(color='#00ff41')))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
if st.checkbox("Afficher les dossiers d'expertise"):
    df_logs = pd.read_sql_query("SELECT timestamp, pseudo, context, kmass, status, payload FROM audit_logs ORDER BY id DESC", st.session_state.db)
    st.dataframe(df_logs, use_container_width=True)
