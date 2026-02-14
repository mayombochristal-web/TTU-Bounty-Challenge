import streamlit as st
import numpy as np
import pandas as pd
import hashlib
import time
import secrets
from datetime import datetime

# --- CONFIGURATION HAUTE PERFORMANCE ---
st.set_page_config(
    page_title="TTU-Shield : Ultra-Sentinel Pro",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thème Cyber-Security Personnalisé
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #00ff41; }
    .stMetric { background-color: #0d1117; border: 1px solid #00ff41; padding: 15px; border-radius: 8px; }
    .stTextArea textarea { background-color: #07080a; color: #00ff41; border: 1px solid #00ff41; font-family: 'Consolas', monospace; }
    .stDataFrame { border: 1px solid #1a1c24; }
    </style>
    """, unsafe_allow_html=True)

class UltraSentinel:
    def __init__(self):
        # Clé maître générée à chaque session pour empêcher le reverse-engineering
        self.master_key = secrets.token_hex(32)
        self.history = [0.0] * 50
        self.velocity_history = [0.0] * 50

    def get_dynamic_salt(self):
        """Mutation temporelle (changement toutes les 250ms)"""
        # Crée un décalage imprévisible qui rend le seuil K mouvant
        ts = str(int(time.time() * 4)) 
        h = hashlib.sha256((self.master_key + ts).encode()).hexdigest()
        return (int(h[:2], 16) / 255) * 0.02 # Micro-ajustement dynamique

    def analyze_pro(self, payload):
        if not payload: return 0.0, 0.0, "STABLE"
        
        # 1. ANALYSE SÉMANTIQUE (Distinction Humain vs Code)
        # On identifie les caractères alphabétiques et les espaces
        alpha_chars = sum(c.isalpha() or c.isspace() for c in payload)
        total_len = len(payload)
        human_ratio = alpha_chars / total_len if total_len > 0 else 0
        
        # 2. PONDÉRATION GÉOMÉTRIQUE DES SYMBOLES (Cyber-Signature)
        critical_symbols = ";|&<>$'\"\\{}[]()_="
        # Un symbole critique pèse 50 fois plus qu'une lettre standard
        weight = sum(5.0 if char in critical_symbols else 0.1 for char in payload)
        
        # 3. MESURE DE L'ENTROPIE (Instabilité des données)
        prob = [float(payload.count(c)) / total_len for c in set(payload)]
        entropy = -sum([p * np.log2(p) for p in prob])
        
        # 4. FORMULE DE CALCUL ADAPTATIVE
        # Si le contenu est majoritairement humain (ratio > 0.85), on réduit la sensibilité
        sensitivity = 0.15 if human_ratio > 0.85 else 1.0
        
        k_pure = (weight * entropy * sensitivity) / (total_len + 1)
        k_final = k_pure + self.get_dynamic_salt()
        
        # Calcul de la vitesse de phase (Vibration du signal)
        velocity = abs(k_final - self.history[-1])
        
        # Mise à jour des registres
        self.history.append(k_final)
        self.velocity_history.append(velocity)
        if len(self.history) > 50:
            self.history.pop(0)
            self.velocity_history.pop(0)
            
        # DÉFINITION DES SEUILS (CALIBRÉS PRO)
        if k_final > 0.70 or velocity > 0.25: return k_final, velocity, "CRITICAL"
        if k_final > 0.35: return k_final, velocity, "WARNING"
        return k_final, velocity, "STABLE"

# --- INITIALISATION DE LA SESSION ---
if 'sentinel' not in st.session_state:
    st.session_state.sentinel = UltraSentinel()
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- INTERFACE UTILISATEUR ---
st.title("🛡️ TTU-Shield : Ultra-Sentinel Pro")
st.markdown("*Système de défense immunitaire contre les injections et le chaos sémantique.*")

# Analyse de l'entrée précédente (si existe)
current_payload = st.session_state.get('last_input', "")
k_val, v_val, status = st.session_state.sentinel.analyze_pro(current_payload)

# Zone des métriques
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("VECTEUR K (Masse)", f"{k_val:.5f}")
with col2:
    st.metric("VITESSE PHASE (Vibration)", f"{v_val:.5f}")
with col3:
    status_color = {"CRITICAL": "red", "WARNING": "orange", "STABLE": "green"}
    st.markdown(f"**SÉCURITÉ :** :{status_color[status]}[{status}]")

st.divider()

# Layout Principal
left_col, right_col = st.columns([1, 1])

with left_col:
    st.header("🖥️ Console de Flux")
    data_input = st.text_area("Entrée de données (Texte, SQL, Script...)", height=180, placeholder="Analysez un flux entrant...")
    
    if st.button("LANCER L'AUDIT DU VECTEUR"):
        st.session_state.last_input = data_input
        k, v, s = st.session_state.sentinel.analyze_pro(data_input)
        
        if s != "STABLE":
            new_log = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Vector K": round(k, 4),
                "Threat": s,
                "Action": "Dissipated"
            }
            st.session_state.logs.append(new_log)
        st.rerun()

with right_col:
    st.header("📊 Analyse Temporelle")
    # Fusion des données pour le graphique
    df_chart = pd.DataFrame({
        "Viscosité (K)": st.session_state.sentinel.history,
        "Vitesse (dk/dt)": st.session_state.sentinel.velocity_history
    })
    st.line_chart(df_chart, color=["#00ff41", "#ff4b4b"])

# Section des Logs exportables
st.divider()
st.header("📋 Registre d'Audit de Sécurité")
if st.session_state.logs:
    df_logs = pd.DataFrame(st.session_state.logs)
    st.dataframe(df_logs.tail(10), use_container_width=True)
    
    # Bouton d'export CSV pour les rapports pro
    csv = df_logs.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger les logs d'attaque (CSV)", csv, "sentinel_logs.csv", "text/csv")
else:
    st.info("Aucune anomalie détectée dans le flux actuel.")

st.sidebar.title("Configuration Pro")
st.sidebar.write("**Mode :** Défense Active")
st.sidebar.write("**Algorithme :** TTU-MC3 Evolution")
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 TTU-Cyber-Security Systems. Tous droits réservés.")
