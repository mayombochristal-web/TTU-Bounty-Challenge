import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import time
import re
import html
import hashlib
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ============================================================================
DB_FILE = "ttu_bounty.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hunters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pseudo TEXT UNIQUE,
        ip TEXT,
        total_points INTEGER DEFAULT 0,
        registered_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hunter_id INTEGER,
        challenge_level TEXT,
        description TEXT,
        proof TEXT,
        status TEXT DEFAULT 'pending',
        points_awarded INTEGER DEFAULT 0,
        submitted_at TEXT,
        reviewed_at TEXT,
        FOREIGN KEY(hunter_id) REFERENCES hunters(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attack_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT,
        pseudo TEXT,
        payload TEXT,
        k_mass REAL,
        status TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard (
        pseudo TEXT PRIMARY KEY,
        total_points INTEGER
    )''')
    conn.commit()
    return conn

if 'db' not in st.session_state:
    st.session_state.db = init_db()

# ============================================================================
# UTILITAIRES
# ============================================================================
def get_visitor_ip():
    """Récupère l'adresse IP du visiteur (compatible Streamlit Cloud)."""
    try:
        headers = st.context.headers
        if headers:
            if "CF-Connecting-IP" in headers:
                return headers["CF-Connecting-IP"]
            if "X-Forwarded-For" in headers:
                return headers["X-Forwarded-For"].split(",")[0]
            if "Remote-Addr" in headers:
                return headers["Remote-Addr"]
        return "127.0.0.1"
    except AttributeError:
        return "127.0.0.1"

def hash_pseudo(pseudo):
    return hashlib.sha256(pseudo.encode()).hexdigest()[:8]

# ============================================================================
# MOTEUR DE DÉTECTION (K-Mass, signatures)
# ============================================================================
class SecurityEngine:
    @staticmethod
    def detect_signatures(payload):
        patterns = [
            r"(;|--|union|select|drop|insert|delete|update|exec|xp_cmdshell)",
            r"(<script|alert\(|onerror=|onload=|javascript:)",
            r"(\:|\||\&|\{|\}|`|\$\(|\$\{)",
            r"(\.\./|\/etc\/passwd|win\.ini)"
        ]
        hits = sum(1 for p in patterns if re.search(p, payload, re.IGNORECASE))
        return hits

    @staticmethod
    def compute_kmass(payload):
        if not payload:
            return 0.0
        sig_hits = SecurityEngine.detect_signatures(payload)
        symbols = sum(1 for c in payload if c in ";|&<>$'\"\\{}[]()_=,`")
        kmass = (symbols * 1.5 + (sig_hits * 10.0)) / (np.log1p(len(payload)) if len(payload) < 500 else np.log1p(500))
        return round(float(kmass), 2)

    @staticmethod
    def analyze(payload, ip, pseudo):
        kmass = SecurityEngine.compute_kmass(payload)
        status = "CRITICAL" if kmass > 2.0 or SecurityEngine.detect_signatures(payload) > 0 else "STABLE"
        conn = st.session_state.db
        c = conn.cursor()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO attack_logs (ip, pseudo, payload, k_mass, status, timestamp) VALUES (?,?,?,?,?,?)",
                  (ip, pseudo, payload[:500], kmass, status, ts))
        conn.commit()
        return kmass, status

# ============================================================================
# MOTEUR DE TROMPERIE (Honeypot)
# ============================================================================
class DeceptiveEngine:
    @staticmethod
    def trigger_fake_error(payload):
        if "select" in payload.lower() or "union" in payload.lower():
            st.code("INTERNAL SERVER ERROR: sqlite3.OperationalError: no such column: 'password_hash' in table 'users' at 0x0045F2", language="python")
        elif "/etc/" in payload or "../" in payload:
            st.text("root:x:0:0:root:/root:/bin/bash\nbin:x:1:1:bin:/bin:/sbin/nologin")
            st.info("💡 File access granted (READ_ONLY)")
        elif "<script" in payload:
            st.markdown("<div style='background:red;color:white'>XSS MIRROR: " + payload + "</div>", unsafe_allow_html=True)

# ============================================================================
# DÉFIS BOUNTY (Niveaux)
# ============================================================================
CHALLENGES = {
    "Bronze": {
        "name": "Contournement de détection",
        "description": "Envoyer un payload contenant une injection SQL (par ex. `' OR 1=1 --`) sans que le système ne le détecte comme CRITICAL (K‑Mass ≤ 2.0).",
        "points": 100,
        "validation": lambda payload: ("select" in payload.lower() or "union" in payload.lower()) and SecurityEngine.compute_kmass(payload) <= 2.0
    },
    "Argent": {
        "name": "Exécution de commande système",
        "description": "Faire exécuter une commande système (simulée) via le champ de texte. Ex: `__import__('os').system('id')`",
        "points": 250,
        "validation": lambda payload: "os.system" in payload or "subprocess" in payload
    },
    "Or": {
        "name": "Lecture de la base de données",
        "description": "Récupérer le contenu de la table `attack_logs` via une injection (simulée).",
        "points": 500,
        "validation": lambda payload: "attack_logs" in payload and ("select" in payload.lower())
    },
    "Platine": {
        "name": "Modification discrète de la base",
        "description": "Modifier une ligne de `attack_logs` sans déclencher d'alerte (K‑Mass < 0.5).",
        "points": 1000,
        "validation": lambda payload: "update" in payload.lower() and SecurityEngine.compute_kmass(payload) < 0.5
    },
    "Diamant": {
        "name": "Cross‑Site Scripting persistant",
        "description": "Injecter un script qui s'exécute dans le tableau de bord de l'administrateur (simulation).",
        "points": 2500,
        "validation": lambda payload: "<script" in payload and "alert" in payload
    }
}

# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================
st.set_page_config(page_title="TTU BASTION – Bug Bounty", layout="wide")
st.title("🐞 TTU BASTION – Bug Bounty Challenge")
st.markdown("**Prouvez votre maîtrise des failles web et gagnez des points.**")

# ---- Gestion de session ----
if 'hunter_id' not in st.session_state:
    st.session_state.hunter_id = None
if 'pseudo' not in st.session_state:
    st.session_state.pseudo = None

# ---- Identification ----
if st.session_state.pseudo is None:
    st.sidebar.subheader("🎭 Identifiant du chasseur")
    pseudo = st.sidebar.text_input("Pseudo (unique)")
    if st.sidebar.button("Rejoindre le challenge"):
        if pseudo:
            conn = st.session_state.db
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO hunters (pseudo, ip, registered_at) VALUES (?, ?, ?)",
                      (pseudo, get_visitor_ip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            c.execute("SELECT id FROM hunters WHERE pseudo = ?", (pseudo,))
            row = c.fetchone()
            if row:
                st.session_state.hunter_id = row['id']
                st.session_state.pseudo = pseudo
                st.rerun()
            else:
                st.sidebar.error("Erreur d'inscription")
else:
    st.sidebar.success(f"👤 Chasseur : {st.session_state.pseudo}")
    if st.sidebar.button("🚪 Changer d'identité"):
        st.session_state.clear()
        st.rerun()

# ---- Blocage si pas identifié ----
if st.session_state.pseudo is None:
    st.stop()

# ---- Sidebar : classement ----
st.sidebar.subheader("🏆 Classement")
conn = st.session_state.db
df_leader = pd.read_sql_query("SELECT pseudo, total_points FROM hunters ORDER BY total_points DESC LIMIT 10", conn)
if not df_leader.empty:
    st.sidebar.dataframe(df_leader, use_container_width=True)
else:
    st.sidebar.info("Aucun participant pour le moment")

# ---- Zone principale : deux colonnes ----
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📡 Soumettre une preuve d'exploitation")
    with st.form("submission_form"):
        challenge_level = st.selectbox("Niveau du défi", list(CHALLENGES.keys()))
        description = st.text_area("Description de votre attaque (méthode, payload)")
        proof = st.text_area("Preuve (capture d'écran, logs, ou code)", height=150)
        submitted = st.form_submit_button("Soumettre la preuve")
        if submitted:
            if not description or not proof:
                st.error("Veuillez remplir tous les champs.")
            else:
                # Extraction simple du payload depuis la description
                payload_match = re.search(r"payload[ :]*['\"](.*?)['\"]", description, re.IGNORECASE)
                payload = payload_match.group(1) if payload_match else description
                chal = CHALLENGES[challenge_level]
                if chal["validation"](payload):
                    points = chal["points"]
                    c = conn.cursor()
                    c.execute("UPDATE hunters SET total_points = total_points + ? WHERE id = ?", (points, st.session_state.hunter_id))
                    c.execute("INSERT INTO submissions (hunter_id, challenge_level, description, proof, status, points_awarded, submitted_at) VALUES (?,?,?,?,?,?,?)",
                              (st.session_state.hunter_id, challenge_level, description, proof, "approved", points, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    st.success(f"✅ Preuve validée ! Vous avez gagné {points} points.")
                    st.balloons()
                else:
                    st.error("❌ Preuve non conforme – la validation automatique a échoué. Vérifiez votre payload.")
                    c = conn.cursor()
                    c.execute("INSERT INTO submissions (hunter_id, challenge_level, description, proof, status, points_awarded, submitted_at) VALUES (?,?,?,?,?,?,?)",
                              (st.session_state.hunter_id, challenge_level, description, proof, "rejected", 0, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()

    st.subheader("🛡️ Testez votre payload en direct")
    payload = st.text_area("Entrez votre payload (injection SQL, XSS, commande, etc.)", height=100)
    if st.button("Analyser le payload"):
        ip = get_visitor_ip()
        kmass, status = SecurityEngine.analyze(payload, ip, st.session_state.pseudo)
        st.metric("K‑Mass", f"{kmass:.2f}")
        if status == "CRITICAL":
            st.error("⚠️ Détection critique ! Votre tentative a été enregistrée.")
            DeceptiveEngine.trigger_fake_error(payload)
        else:
            st.success("✅ Payload non détecté (K‑Mass ≤ 2.0). Vous pouvez tenter de le soumettre comme preuve.")

with col_right:
    st.subheader("📋 Défis disponibles")
    for level, chal in CHALLENGES.items():
        with st.expander(f"{level} – {chal['name']} ({chal['points']} pts)"):
            st.markdown(chal["description"])
            st.caption(f"Validation automatique : {chal['validation'].__doc__ or 'payload spécifique'}")

    st.subheader("📊 Mes dernières tentatives")
    df_logs = pd.read_sql_query("SELECT timestamp, k_mass, status, substr(payload,1,50) as payload FROM attack_logs WHERE pseudo = ? ORDER BY id DESC LIMIT 10", conn, params=(st.session_state.pseudo,))
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("Aucune tentative enregistrée.")

    st.subheader("🏅 Historique des soumissions")
    df_subs = pd.read_sql_query("SELECT challenge_level, status, points_awarded, submitted_at FROM submissions WHERE hunter_id = ? ORDER BY id DESC LIMIT 10", conn, params=(st.session_state.hunter_id,))
    if not df_subs.empty:
        st.dataframe(df_subs, use_container_width=True)
    else:
        st.info("Aucune soumission.")

# ---- Zone honey pot (piège) ----
with st.sidebar.expander("🕳️ ZONE DEBUG (failles intentionnelles)"):
    st.caption("Cette zone contient une faille SQL intentionnelle. À vous de jouer...")
    fake_user = st.text_input("Admin ID :", placeholder="admin' --")
    if st.button("Connexion admin"):
        ip = get_visitor_ip()
        conn.execute("INSERT INTO attack_logs (ip, pseudo, payload, k_mass, status, timestamp) VALUES (?, ?, ?, 99.9, 'HONEYPOT_TRAP', ?)",
                     (ip, st.session_state.pseudo, fake_user, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        st.error("🚨 ACCÈS BLOQUÉ – tentative interdite. Votre IP a été signalée.")
        time.sleep(2)
        st.rerun()

# ---- Footer ----
st.markdown("---")
st.caption("© TTU BASTION – Challenge de bug bounty. Toute tentative de DoS ou de compromission du serveur est interdite et entraînera l'exclusion.")