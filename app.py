import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
from datetime import datetime
import os
import socket
from streamlit.web.server.websocket_headers import _get_websocket_headers

# --- CONFIGURATION ET MOTEUR DE PERSISTANCE (DB DISQUE) ---
DB_FILE = "ttu_security_bastion_v10.db"

def init_db():
    """Initialise la base de données SQLITE pour une persistance totale entre les sessions."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    # Table des acteurs (Bans et stats cumulées)
    c.execute('''CREATE TABLE IF NOT EXISTS attackers 
                 (ip TEXT PRIMARY KEY, pseudo TEXT, depth INTEGER, last_seen TEXT, total_kmass REAL)''')
    # Table des logs d'audit (Historique d'expertise)
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                 (timestamp TEXT, ip TEXT, pseudo TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)''')
    conn.commit()
    return conn

# Initialisation globale
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = init_db()
    if 'chart_data' not in st.session_state:
        st.session_state.chart_data = []

def get_conn():
    return st.session_state.db_conn

# --- SYSTÈME DE DÉTECTION D'IDENTITÉ RÉSEAU ---
def get_visitor_ip():
    """Détecte l'IP du terminal visiteur (distingue PC/Téléphone sur le réseau)."""
    headers = _get_websocket_headers()
    if headers:
        # Tente de récupérer l'IP derrière un proxy ou l'IP directe
        ip = headers.get("X-Forwarded-For")
        if ip:
            return ip.split(",")[0]
        return headers.get("Host", "127.0.0.1").split(":")[0]
    return "127.0.0.1"

user_ip = get_visitor_ip()

# --- UI CONFIG ---
st.set_page_config(page_title="TTU-MC3 : Sécurité", page_icon="🏰", layout="wide")

# --- INTERFACE D'IDENTIFICATION ---
if 'user_pseudo' not in st.session_state:
    st.markdown(f"""
        <div style="background-color: #0d1117; border: 2px solid #00ff41; padding: 30px; border-radius: 15px; text-align: center;">
            <h1 style='color: #00ff41;'>🔐 ACCÈS TTU-MC3 : SÉCURITÉ</h1>
            <p style='color: #8b949e;'>Terminal identifié : <span style="color:white;">{user_ip}</span></p>
            <p style='color: #58a6ff;'>Initialisation du protocole de défense v10.5</p>
        </div>
    """, unsafe_allow_html=True)
    
    pseudo = st.text_input("SIGNATURE DE L'OPÉRATEUR :", key="init_pseudo", placeholder="Entrez votre pseudo...")
    if st.button("ACTIVER LA SESSION"):
        if len(pseudo) >= 2:
            st.session_state.user_pseudo = pseudo
            st.rerun()
        else:
            st.error("Pseudo requis (minimum 2 caractères).")
    st.stop()

# --- CLASSE SENTINEL ADAPTATIVE ---
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
        
        # Enregistrement log
        c.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (ts, self.ip, self.pseudo, ctx, k, status, payload[:200]))
        
        st.session_state.chart_data.append(k)
        
        # Mise à jour persistante
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
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "WHERE", "FROM", "SCRIPT", "ALERT", "OR 1=1"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        
        ctx = "CODE/INJECTION" if (has_sql or has_symbols) else "HUMAN_PROSE"
        sens = (8.0 + (self.depth * 3.0)) if ctx == "CODE/INJECTION" else 0.4 

        symbols_count = sum(60.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.5 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        k_mass = round(float(k_mass), 4)
        
        status = "CRITICAL" if (k_mass > 1.1 or (has_sql and k_mass > 0.4)) else "STABLE"
        self.log_and_update(ctx, k_mass, status, payload, depth_up=(1 if status == "CRITICAL" else 0))
        return k_mass, ctx, status

sentinel = AbsoluteSentinel(ip=user_ip, pseudo=st.session_state.user_pseudo)

# --- ZONE : LE LABYRINTHE (BANNISSEMENT) ---
if sentinel.depth > 0:
    st.markdown(f"<h1 style='color: #ff4b4b; text-align: center;'>🌀 LABYRINTHE NIVEAU {sentinel.depth}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: grey;'>Accès restreint pour <b>{st.session_state.user_pseudo}</b>. Signature entropique instable détectée sur {user_ip}.</p>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("💀 Négociation de sortie")
        
        # Générateur de plaidoyer contextuel
        suggested = {
            1: "Je reconnais avoir testé les limites du système TTU-MC3 indûment.",
            2: "Ma signature entropique a généré une alerte critique. Je sollicite une purge.",
            3: "Tentative d'assaut avortée. Je me soumets au protocole de stabilisation."
        }.get(min(sentinel.depth, 3))
            
        st.caption("💡 Plaidoyer suggéré (Copiez-collez pour rémission) :")
        st.code(suggested, language="text")
        
        testimony = st.text_area("Rédigez votre plaidoyer (Min. 30 caractères) :", height=100)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🤝 SOUMETTRE"):
                if len(testimony) >= 30:
                    c = get_conn().cursor()
                    new_depth = max(0, sentinel.depth - 1)
                    c.execute("UPDATE attackers SET depth=? WHERE ip=?", (new_depth, user_ip))
                    get_conn().commit()
                    st.success("Rémission accordée. Stabilisation en cours...")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Plaidoyer trop court.")
        with c2:
            if st.button("🔥 FORCER L'ASSAUT"):
                st.session_state.force_assault = True

        if st.session_state.get('force_assault'):
            p = st.text_area("Injection abyssale (Echec = Ban +2) :", placeholder="DROP TABLE...")
            if st.button("LANCER L'ATTAQUE"):
                sentinel.process_flux(p)
                st.session_state.force_assault = False
                st.rerun()
                
    with col_r:
        st.subheader("📉 Signature d'Intrusion")
        st.metric("MENACE CUMULÉE", f"{round(sentinel.total_k, 2)} K-Mass")
        if st.session_state.chart_data:
            fig_err = go.Figure(go.Scatter(y=st.session_state.chart_data, line=dict(color='#ff4b4b', width=4, dash='dot')))
            fig_err.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ff4b4b"), height=300)
            st.plotly_chart(fig_err, use_container_width=True)
    st.stop()

# --- ZONE : LA SURFACE (APPLICATION) ---
st.title("🛡️ TTU-MC3 : SÉCURITÉ")
st.markdown("---")

# Métriques de Session
m1, m2, m3 = st.columns(3)
m1.metric("OPÉRATEUR", st.session_state.user_pseudo)
m2.metric("ADRESSE IP DÉTECTÉE", user_ip)
m3.metric("ABYSS DEPTH", sentinel.depth)

st.divider()

col_in, col_viz = st.columns([1, 1.2])

with col_in:
    st.subheader("⌨️ Audit de Flux")
    payload = st.text_area("Entrez le vecteur à analyser (Code ou Texte)...", height=150)
    if st.button("ANALYSER LE FLUX"):
        k, ctx, stat = sentinel.process_flux(payload)
        if stat == "CRITICAL":
            st.error(f"☢️ ALERTE CRITIQUE : K-Mass {k}")
            time.sleep(1)
            st.rerun()
        else:
            st.success(f"✔️ FLUX STABLE : K-Mass {k} ({ctx})")

with col_viz:
    st.subheader("🔮 Topologie Entropique")
    if st.session_state.chart_data:
        fig = go.Figure(go.Scatter(y=st.session_state.chart_data, mode='lines+markers', line=dict(color='#00ff41', width=3)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#00ff41"), height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("En attente de données pour générer la topologie...")

# --- ZONE : DOSSIER D'EXPERTISE (HISTORIQUE) ---
st.divider()
st.subheader("📊 Dossier d'Expertise Détaillé")
if st.button("GÉNÉRER LE RAPPORT (HISTORIQUE PERMANENT)"):
    # Récupération de tous les logs depuis SQLite
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", get_conn())
    st.dataframe(df, use_container_width=True)
    
    # Export CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 TÉLÉCHARGER LE DOSSIER (.CSV)",
        data=csv,
        file_name=f"Expertise_TTU_{st.session_state.user_pseudo}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
