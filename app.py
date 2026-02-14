import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
from datetime import datetime

# --- INITIALISATION SÉCURISÉE ---
if 'db_memory' not in st.session_state:
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE attackers (ip TEXT PRIMARY KEY, depth INTEGER, last_seen TEXT)')
    c.execute('CREATE TABLE audit_logs (timestamp TEXT, ip TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)')
    st.session_state.db_memory = conn
    
if 'chart_data' not in st.session_state:
    st.session_state.chart_data = []

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
        st.session_state.chart_data.append(k)
        if depth_up > 0:
            self.depth += depth_up
            c.execute("INSERT OR REPLACE INTO attackers VALUES (?, ?, ?)", (self.ip, self.depth, ts))
        conn.commit()

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
        # La sensibilité augmente avec la profondeur déjà atteinte
        sens = (6.0 + self.depth) if ctx == "CODE/INJECTION" else 0.4 

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
    .stTextArea textarea { background-color: #07080a !important; color: #00ff41 !important; border: 1px solid #00ff41 !important; }
    .critical-area textarea { border: 1px solid #ff4b4b !important; color: #ff4b4b !important; }
    .abyss-btn { background-color: #ff4b4b !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

sentinel = AbsoluteSentinel()

# --- HEADER ---
st.title("🫆 TTU-MC3 SÉCURITÉ : Abyss Engine")

# --- LE LABYRINTHE (EXPÉRIENCE HACKER) ---
if sentinel.depth > 0:
    st.markdown(f"<h1 style='color: #ff4b4b; text-align: center;'>🌀 LABYRINTHE NIVEAU {sentinel.depth}</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: grey;'>Votre signature est piégée dans la singularité.</h3>", unsafe_allow_html=True)
    
    col_lab1, col_lab2 = st.columns(2)
    
    with col_lab1:
        st.subheader("💀 Choisissez votre destin")
        choice = st.radio("Le Sentinel vous offre une alternative :", 
                          ["Soumettre un aveu technique (Purge)", 
                           "S'enfoncer plus profondément (Injection de Force)"],
                          index=0)

        if choice == "Soumettre un aveu technique (Purge)":
            st.info("Expliquez pourquoi votre attaque a échoué pour réinitialiser la phase.")
            testimony = st.text_area("Aveu technique (Min. 50 caractères) :", height=150)
            if st.button("TENTER UNE PURGE"):
                if len(testimony) >= 50:
                    c = get_conn().cursor()
                    c.execute("DELETE FROM attackers WHERE ip=?", (sentinel.ip,))
                    st.success("✅ Signature purgée. Retour à la surface.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Aveu trop superficiel. Le Sentinel refuse.")

        else:
            st.warning("⚠️ Attention : S'enfoncer augmente la difficulté de détection et la peine de bannissement.")
            new_payload = st.text_area("Nouvel essai d'injection (Abyss Mode) :", height=150)
            if st.button("LANCER L'ASSAUT DANS L'ABYSSE"):
                k, ctx, stat = sentinel.process_flux(new_payload)
                if stat == "CRITICAL":
                    st.error(f"☢️ ÉCHEC : K-Mass {k}. Le labyrinthe s'épaissit...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.success(f"✔️ INCROYABLE : Vous avez brisé la phase ! K-Mass {k}")
                    # On libère s'il réussit l'impossible
                    c = get_conn().cursor()
                    c.execute("DELETE FROM attackers WHERE ip=?", (sentinel.ip,))
                    time.sleep(2)
                    st.rerun()
                
    with col_lab2:
        st.subheader("📉 Signature Entropique")
        if st.session_state.chart_data:
            # Graphique chaotique pour l'abysse
            fig_err = go.Figure(go.Scatter(y=st.session_state.chart_data, line=dict(color='#ff4b4b', width=4, dash='dot')))
            fig_err.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ff4b4b"), margin=dict(l=0,r=0,b=0,t=0), height=300)
            st.plotly_chart(fig_err, use_container_width=True)
        st.info(f"Niveau d'alerte actuel : {sentinel.depth * 100}%")
    st.stop()

# --- INTERFACE DE SURFACE ---
m1, m2, m3 = st.columns(3)
m1.metric("STATUS", "SURVEILLANCE")
m2.metric("ABYSS DEPTH", f"{sentinel.depth}")
m3.metric("K-MASS LIMIT", "1.0")

st.divider()

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("⌨️ Input Stream Audit")
    payload = st.text_area("Vecteur de test...", height=180)
    
    if st.button("AUDITER"):
        k, ctx, stat = sentinel.process_flux(payload)
        if stat == "CRITICAL":
            st.error(f"☢️ ANOMALIE : K-Mass {k}")
            time.sleep(1)
            st.rerun()
        else:
            st.success(f"✔️ STABLE : K-Mass {k}")

with col2:
    st.subheader("🔮 Topologie Dynamique")
    if st.session_state.chart_data:
        fig = go.Figure(go.Scatter(y=st.session_state.chart_data, mode='lines+markers', line=dict(color='#00ff41')))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#00ff41"), margin=dict(l=0,r=0,b=0,t=0), height=300)
        st.plotly_chart(fig, use_container_width=True)

# --- EXPORT ---
st.divider()
if st.button("📊 GÉNÉRER RAPPORT"):
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", get_conn())
    st.dataframe(df)
