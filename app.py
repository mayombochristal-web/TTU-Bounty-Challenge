import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
from datetime import datetime

# --- INITIALISATION DE LA BASE EN MÉMOIRE (ZERO CRASH) ---
# On utilise le session_state pour simuler la persistance sans les verrous de fichiers
if 'db_memory' not in st.session_state:
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE attackers (ip TEXT PRIMARY KEY, depth INTEGER, last_seen TEXT)')
    c.execute('CREATE TABLE audit_logs (timestamp TEXT, ip TEXT, context TEXT, kmass REAL, status TEXT, payload TEXT)')
    st.session_state.db_memory = conn

def get_conn():
    return st.session_state.db_memory

# --- CLASSE SENTINEL AMÉLIORÉE ---
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
        # Insertion des logs
        c.execute("INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?)", 
                  (ts, self.ip, ctx, k, status, payload[:100]))
        # Mise à jour du bannissement
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
        if not payload: return 0.0, "NONE", "STABLE", "Attente..."
        
        # CORRECTIF FAILLES PRÉCÉDENTES (SQL + Dilution)
        sql_keywords = ["SELECT", "DROP", "UNION", "DELETE", "INSERT", "UPDATE", "TABLE", "WHERE"]
        has_sql = any(k in payload.upper() for k in sql_keywords)
        has_symbols = any(c in ";()[]{}<>" for c in payload)
        
        ctx = "CODE/INJECTION" if (has_sql or has_symbols) else "HUMAN_PROSE"
        sens = 6.0 if ctx == "CODE/INJECTION" else 0.4 # Augmentation sévérité

        symbols_count = sum(45.0 if c in ";|&<>$'\"\\{}[]()_=" else 0.4 for c in payload)
        zipf_score = self.analyze_frequency(payload)
        
        # Division Logarithmique pour empêcher la dilution par la longueur
        k_mass = (symbols_count * zipf_score * sens) / np.log1p(len(payload))
        k_mass = round(float(k_mass), 4)
        
        status = "STABLE"
        depth_to_add = 0
        if k_mass > 1.0 or (has_sql and k_mass > 0.3):
            status = "CRITICAL"
            depth_to_add = 1
        
        self.log_and_update(ctx, k_mass, status, payload, depth_up=depth_to_add)
        return k_mass, ctx, status

# --- UI INTERFACE ---
st.set_page_config(page_title="TTU-Shield v6.4", page_icon="🛡️", layout="wide")
sentinel = AbsoluteSentinel()

st.title("🛡️ TTU-Shield v6.4 : Infinity-Stream")
st.info("Système stabilisé : Base de données en mémoire vive (Zero-Lock Engine).")

# --- LE LABYRINTHE ---
if sentinel.depth > 0:
    st.markdown(f"## 🌀 LABYRINTHE NIVEAU {sentinel.depth}")
    st.error("Accès révoqué par analyse de phase.")
    if st.button("RÉINITIALISER MA SIGNATURE"):
        c = get_conn().cursor()
        c.execute("DELETE FROM attackers WHERE ip=?", (sentinel.ip,))
        st.rerun()
    st.stop()

# --- ANALYSEUR ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("⌨️ Input Stream")
    payload = st.text_area("Donnée à auditer :", height=150)
    if st.button("AUDITER LE VECTEUR"):
        k, ctx, stat = sentinel.process_flux(payload)
        if stat == "CRITICAL":
            st.error(f"ALERTE : INTRUSION DÉTECTÉE (K-Mass: {k})")
            time.sleep(1)
            st.rerun()
        else:
            st.success(f"VALIDE : Flux sain (K-Mass: {k})")

with col2:
    st.subheader("📊 Métriques de Phase")
    # Graphique dynamique basé sur les logs
    c = get_conn().cursor()
    c.execute("SELECT kmass FROM audit_logs LIMIT 20")
    data = [r[0] for r in c.fetchall()]
    if data:
        st.line_chart(data)
    else:
        st.write("En attente de données...")

# --- EXPORT CSV ---
st.divider()
if st.button("📊 GÉNÉRER RAPPORT D'AUDIT CSV"):
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", get_conn())
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger CSV", csv, "audit_sentinel.csv", "text/csv")
