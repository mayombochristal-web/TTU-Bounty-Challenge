import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
from datetime import datetime

# --- INITIALISATION SÉCURISÉE (CORRECTION STRUCTURE) ---
# Si vous changez la structure, il faut parfois vider le cache ou forcer la réinitialisation
if 'db_memory' not in st.session_state:
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    c = conn.cursor()
    # Structure à 7 colonnes incluant le PSEUDO
    c.execute('CREATE TABLE attackers (ip TEXT PRIMARY KEY, pseudo TEXT, depth INTEGER, last_seen TEXT)')
    c.execute('CREATE TABLE audit_logs (timestamp TEXT, ip TEXT, pseudo TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)')
    st.session_state.db_memory = conn
    st.session_state.chart_data = []

def get_conn():
    return st.session_state.db_memory

# --- SYSTÈME D'IDENTIFICATION ---
if 'user_pseudo' not in st.session_state:
    st.markdown("""
        <div style="background-color: #0d1117; border: 2px solid #00ff41; padding: 30px; border-radius: 15px; text-align: center;">
            <h1 style='color: #00ff41;'>🔐 ACCÈS TTU-MC3 SÉCURITÉ</h1>
            <p style='color: #8b949e;'>Initialisation du profil d'expertise requise.</p>
        </div>
    """, unsafe_allow_html=True)
    
    pseudo = st.text_input("NOM DE L'OPÉRATEUR / SIGNATURE HACKER :", key="init_pseudo")
    if st.button("ACTIVER LA SESSION"):
        if len(pseudo) >= 2:
            st.session_state.user_pseudo = pseudo
            st.rerun()
        else:
            st.error("Pseudo requis (min. 2 caractères).")
    st.stop()

# --- CLASSE SENTINEL OMNISCIENTE ---
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
        # INSERTION À 7 COLONNES (Synchronisée avec CREATE TABLE)
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
        depth_to_add = 1 if status == "CRITICAL" else 0
        
        self.log_and_update(ctx, k_mass, status, payload, depth_up=depth_to_add)
        return k_mass, ctx, status

# --- CONFIGURATION UI ---
st.set_page_config(page_title="TTU-MC3 SÉCURITÉ", page_icon="🫆", layout="wide")
user_ip = "STATION-REMOTE" # Note: L'IP réelle nécessite des librairies spécifiques sur Cloud
sentinel = AbsoluteSentinel(ip=user_ip, pseudo=st.session_state.user_pseudo)

# --- LE LABYRINTHE ---
if sentinel.depth > 0:
    st.markdown(f"<h1 style='color: #ff4b4b; text-align: center;'>🌀 LABYRINTHE NIVEAU {sentinel.depth}</h1>", unsafe_allow_html=True)
    st.error(f"IDENTITÉ COMPROMISE : {st.session_state.user_pseudo} @ {user_ip}")
    
    col_l, col_r = st.columns(2)
    with col_l:
        choice = st.radio("Destin :", ["Purge par Aveu", "Assaut Abyssal"])
        if choice == "Purge par Aveu":
            testimony = st.text_area("Témoignez de l'efficacité de l'algorithme (50 chars min) :")
            if st.button("PURGER"):
                if len(testimony) >= 50:
                    get_conn().execute("DELETE FROM attackers WHERE ip=?", (user_ip,))
                    st.success("Signature réalignée.")
                    time.sleep(1)
                    st.rerun()
        else:
            p = st.text_area("Nouvelle injection :")
            if st.button("ASSAUT"):
                k, c, s = sentinel.process_flux(p)
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
c3.metric("PROF. ABYSSE", sentinel.depth)

st.divider()

col_in, col_viz = st.columns([1, 1.2])
with col_in:
    payload = st.text_area("Audit de vecteur...", height=150)
    if st.button("LANCER L'AUDIT"):
        k, ctx, stat = sentinel.process_flux(payload)
        if stat == "CRITICAL": st.rerun()
        else: st.success(f"STABLE (K:{k})")

with col_viz:
    if st.session_state.chart_data:
        fig = go.Figure(go.Scatter(y=st.session_state.chart_data, mode='lines+markers', line=dict(color='#00ff41')))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#00ff41"), height=300)
        st.plotly_chart(fig, use_container_width=True)

# --- EXPORT EXPERTISE ---
st.divider()
if st.button("📊 GÉNÉRER RAPPORT D'EXPERTISE CSV"):
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", get_conn())
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 TÉLÉCHARGER LE RAPPORT", csv, f"Expertise_TTU_{st.session_state.user_pseudo}.csv", "text/csv")
